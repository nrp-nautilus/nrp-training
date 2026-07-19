"""
NRP docs RAG — answer questions about NRP policies and technicalities by
RAG-ing the source-of-truth markdown for https://nrp.ai/documentation/.

What it does:
  1. Sparse-clones the public nrp-site repo (Astro/Starlight Markdown source).
  2. Reads every .md / .mdx under src/content/docs/Documentation, strips
     frontmatter and Astro imports, and recovers a citable nrp.ai URL from
     each filesystem path.
  3. Chunks, embeds with sentence-transformers, stores in Milvus.
  4. Answers a list of NRP-specific questions using either:
       - the NRP managed LLM (OpenAI-compatible)  -> set OPENAI_API_BASE / OPENAI_API_KEY
       - a local Ollama server (mistral)          -> default fallback

Re-running the script reuses the existing Milvus collection unless --reindex
is passed, in which case it drops and rebuilds it.

Run from inside the tutorial-<username>-vectordb pod (or any environment with
network egress, git, and the listed Python deps installed).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)
from sentence_transformers import SentenceTransformer

REPO_URL = "https://gitlab.nrp-nautilus.io/prp/nrp-site.git"
REPO_SUBDIR = "src/content/docs/Documentation"
URL_BASE = "https://nrp.ai/documentation"

EMBED_MODEL = "all-MiniLM-L6-v2"  # 384-dim, runs fine on CPU
EMBED_DIM = 384
COLLECTION = os.environ.get("RAG_COLLECTION", "nrp_docs_rag")
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120

QUESTIONS = [
    "How do I get a Milvus database password on NRP, and what's the connection endpoint?",
    "What are the rules for requesting a GPU on Nautilus, and which GPUs am I allowed to ask for by default?",
    "How do persistent storage classes work on NRP, and which one should I use for general-purpose workloads?",
    "What identity provider does NRP use, and how do I authenticate kubectl from my own laptop after the workshop?",
    "How do I build a custom container image using NRP's GitLab CI?",
    "What does the cluster do if a pod has no CPU or memory limits?",
]


def ensure_repo(repo_dir: Path) -> None:
    """Sparse-clone or update the nrp-site repo, restricted to REPO_SUBDIR."""
    docs_dir = repo_dir / REPO_SUBDIR
    if docs_dir.exists():
        print(f"[1/5] Updating existing clone at {repo_dir}", flush=True)
        subprocess.run(
            ["git", "-C", str(repo_dir), "pull", "--ff-only", "--quiet"],
            check=False,
        )
        return
    print(f"[1/5] Cloning {REPO_URL} (sparse: {REPO_SUBDIR}) -> {repo_dir}", flush=True)
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    subprocess.run(
        [
            "git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
            "--quiet", REPO_URL, str(repo_dir),
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "sparse-checkout", "set", REPO_SUBDIR],
        check=True,
    )


def path_to_url(path: Path, repo_dir: Path) -> str:
    rel = path.relative_to(repo_dir / REPO_SUBDIR)
    parts = list(rel.parts)
    parts[-1] = re.sub(r"\.(md|mdx)$", "", parts[-1])
    if parts[-1].lower() == "index":
        parts = parts[:-1]
    slug = "/".join(parts)
    return f"{URL_BASE}/{slug}".rstrip("/")


_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_IMPORT_RE = re.compile(r"^\s*import\s+.+?from\s+['\"][^'\"]+['\"]\s*;?\s*$", re.MULTILINE)
_ADMONITION_OPEN_RE = re.compile(r":::\w+(?:\[[^\]]*\])?\s*\n")
_ADMONITION_CLOSE_RE = re.compile(r"^:::\s*$", re.MULTILINE)


def strip_mdx(text: str) -> str:
    text = _FRONTMATTER_RE.sub("", text, count=1)
    text = _IMPORT_RE.sub("", text)
    text = _ADMONITION_OPEN_RE.sub("", text)
    text = _ADMONITION_CLOSE_RE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_pages(repo_dir: Path, limit: int | None) -> List[Tuple[str, str]]:
    docs_root = repo_dir / REPO_SUBDIR
    files = sorted([p for p in docs_root.rglob("*") if p.suffix in (".md", ".mdx")])
    if limit:
        files = files[:limit]
    print(f"[2/5] Reading {len(files)} markdown files", flush=True)
    pages: List[Tuple[str, str]] = []
    for p in files:
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"      skip {p}: {e}", flush=True)
            continue
        text = strip_mdx(raw)
        if len(text) < 80:
            continue
        pages.append((path_to_url(p, repo_dir), text))
    print(f"      kept {len(pages)} files (after frontmatter/import strip + length filter)", flush=True)
    return pages


def chunk_pages(pages: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: List[Tuple[str, str]] = []
    for url, text in pages:
        for piece in splitter.split_text(text):
            chunks.append((url, piece))
    print(f"[3/5] Chunked into {len(chunks)} pieces (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})", flush=True)
    return chunks


def milvus_connect() -> None:
    host = os.environ["MILVUS_HOST"]
    port = os.environ.get("MILVUS_PORT", "50051")
    user = os.environ["MILVUS_USER"]
    password = os.environ["MILVUS_PASSWORD"]
    secure = os.environ.get("MILVUS_SECURE", "true").lower() == "true"
    db_name = os.environ["MILVUS_DB_NAME"]
    connections.connect(
        alias="default",
        host=host, port=port, user=user, password=password,
        secure=secure, db_name=db_name,
    )
    print(f"      Milvus connected: {user}@{host}:{port} db={db_name} secure={secure}", flush=True)


def ensure_collection(reindex: bool) -> Collection:
    if utility.has_collection(COLLECTION):
        if reindex:
            print(f"      dropping existing collection {COLLECTION!r}", flush=True)
            utility.drop_collection(COLLECTION)
        else:
            print(f"      reusing existing collection {COLLECTION!r}", flush=True)
            return Collection(COLLECTION)

    fields = [
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBED_DIM),
    ]
    schema = CollectionSchema(fields=fields, description="NRP nrp.ai/documentation RAG corpus (cloned from gitlab nrp-site)")
    coll = Collection(name=COLLECTION, schema=schema)
    coll.create_index(
        field_name="vector",
        index_params={"metric_type": "COSINE", "index_type": "AUTOINDEX", "params": {}},
    )
    print(f"      created collection {COLLECTION!r}", flush=True)
    return coll


def embed_and_insert(coll: Collection, embedder: SentenceTransformer, chunks: List[Tuple[str, str]]) -> None:
    print(f"[4/5] Embedding & inserting {len(chunks)} chunks", flush=True)
    BATCH = 64
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        urls = [u for u, _ in batch]
        texts = [t[:3990] for _, t in batch]
        vectors = embedder.encode(texts, normalize_embeddings=True).tolist()
        coll.insert([urls, texts, vectors])
        if (i // BATCH) % 4 == 0 or i + BATCH >= len(chunks):
            print(f"      inserted {min(i + BATCH, len(chunks))}/{len(chunks)}", flush=True)
    coll.flush()
    coll.load()


def retrieve(coll: Collection, embedder: SentenceTransformer, question: str, k: int = 4):
    qvec = embedder.encode([question], normalize_embeddings=True).tolist()
    results = coll.search(
        data=qvec,
        anns_field="vector",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=k,
        output_fields=["url", "text"],
    )
    return [(hit.entity.get("url"), hit.entity.get("text"), hit.distance) for hit in results[0]]


def make_llm() -> Tuple[OpenAI, str]:
    base = os.environ.get("OPENAI_API_BASE", "https://ellm.nrp-nautilus.io/v1")
    key = os.environ.get("OPENAI_API_KEY", "rifgnLi8QEfRECOgFKVFHaeTLBeSogQ4")
    if base.startswith("https://ellm.nrp-nautilus.io"):
        default_model = "gemma"
    else:
        default_model = "mistral"
    model = os.environ.get("RAG_MODEL", default_model)
    client = OpenAI(base_url=base, api_key=key)
    return client, model


def answer(client: OpenAI, model: str, question: str, hits) -> str:
    context = "\n\n".join(f"Source: {url}\n{text}" for url, text, _ in hits)
    system = (
        "You are an assistant for NRP Nautilus users. Answer the question using ONLY the context. "
        "If the context does not contain the answer, say so. Cite the URL(s) you used."
    )
    user = f"Question: {question}\n\nContext:\n{context}"
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
    )
    return resp.choices[0].message.content or ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reindex", action="store_true", help="Drop and rebuild the Milvus collection")
    ap.add_argument("--limit", type=int, default=None, help="Cap how many doc files to read")
    ap.add_argument("--ask", action="append", help="Ask an extra question (can repeat)")
    ap.add_argument("--only-ask", action="store_true", help="Skip the built-in question set; ask only --ask questions")
    ap.add_argument("--repo-dir", default=os.environ.get("RAG_REPO_DIR", "/tmp/nrp-site"),
                    help="Where to (sparse) clone the nrp-site repo (default /tmp/nrp-site)")
    args = ap.parse_args()

    milvus_connect()

    if args.reindex or not utility.has_collection(COLLECTION):
        repo_dir = Path(args.repo_dir)
        ensure_repo(repo_dir)
        pages = load_pages(repo_dir, args.limit)
        chunks = chunk_pages(pages)
        coll = ensure_collection(reindex=True)
        embedder = SentenceTransformer(EMBED_MODEL)
        embed_and_insert(coll, embedder, chunks)
    else:
        coll = ensure_collection(reindex=False)
        coll.load()
        embedder = SentenceTransformer(EMBED_MODEL)

    questions = (args.ask or []) if args.only_ask else QUESTIONS + (args.ask or [])
    print(f"[5/5] Asking {len(questions)} questions", flush=True)
    client, model = make_llm()
    print(f"      LLM: model={model} base={client.base_url}\n", flush=True)

    for q in questions:
        hits = retrieve(coll, embedder, q, k=4)
        ans = answer(client, model, q, hits)
        print("=" * 78)
        print(f"Q: {q}")
        print("-" * 78)
        print(ans.strip())
        print(f"\nSources used:")
        for url, _, score in hits:
            print(f"  - {url}  (score={score:.3f})")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
