#!/usr/bin/env bash
# CLARIPHY — one-shot setup for the JFC agentic-analysis exercise.
#
# Step 1 of the "Launch the Agent" lesson. It does Parts 1–4 of the JFC exercise
# for you (each is explained in the "Check In on the Agent" lesson):
#   1. installs Claude Code and Pixi (skipped if they are already installed)
#   2. writes a workshop-only Claude Code config that points at NRP
#   3. clones the two repositories and downloads the CMS Open Data samples
#   4. stages the fast-path analysis directory
# and then prints the three commands that launch the agent (Step 2 / Part 5).
#
# Usage (macOS, Linux, or WSL — for native Windows use jfc_setup.ps1):
#
#   bash jfc_setup.sh
#
# It asks for your NRP LLM token (https://nrp.ai/llmtoken). To skip the
# prompt, export it first:  export NRP_LLM_TOKEN="<your-token>"
# Add --yes to never prompt at all (notebooks and other non-interactive use).
#
# Safe to re-run: every step checks what already exists and skips it, and an
# interrupted download resumes where it stopped.
#
# It never edits ~/.claude, ~/.bashrc, ~/.zshrc or any other file of yours.
# Everything it writes lives under ~/jfc-exercise, apart from the claude and
# pixi binaries, which go to their standard ~/.local/bin and ~/.pixi/bin.
# To undo it all after the workshop:  rm -rf ~/jfc-exercise
#
# Optional environment overrides:
#   JFC_WORK      working directory             (default: ~/jfc-exercise)
#   NRP_MODEL     model Claude Code should use  (default: gpt-oss)
#   NRP_CONTEXT   context window for that model (default: 131072)

# This file must run under bash (macOS ships bash 3.2, so no bash-4 features).
if [ -z "${BASH_VERSION:-}" ]; then
    if [ -f "$0" ] && command -v bash >/dev/null 2>&1; then exec bash "$0" "$@"; fi
    echo "Please run this script with bash:  bash jfc_setup.sh" >&2
    exit 1
fi

set -uo pipefail

ASSUME_YES=0
for arg in "$@"; do
    case "$arg" in
        -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
        -y|--yes)  ASSUME_YES=1 ;;
        *)         echo "Unknown option: $arg (try --help)" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
: "${HOME:?HOME is not set}"
WORK="${JFC_WORK:-$HOME/jfc-exercise}"
MODEL="${NRP_MODEL:-gpt-oss}"
CONTEXT="${NRP_CONTEXT:-131072}"
NRP_URL="${JFC_NRP_URL:-https://ellm.nrp-nautilus.io}"      # override only for testing
DATA_URL="${JFC_DATA_URL:-https://s3-west.nrp-nautilus.io/transfer-bucket/h4l-data.tgz}"

CLAUDE_CFG="$WORK/claude-config"
ROGUE="$WORK/jfc/analyses/h4l_rogue"
ENV_FILE="$WORK/nrp-env.sh"

export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
if [ -t 1 ]; then BOLD=$'\033[1m'; RESET=$'\033[0m'; else BOLD=""; RESET=""; fi
step() { printf '\n%s==> %s%s\n' "$BOLD" "$*" "$RESET"; }
ok()   { printf '  ✅ %s\n' "$*"; }
note() { printf '     %s\n' "$*"; }
warn() { printf '  ⚠️  %s\n' "$*"; }
die()  {
    printf '\n  ❌ %s\n' "$1" >&2
    shift
    for line in "$@"; do printf '     %s\n' "$line" >&2; done
    printf '\n     Fix that and re-run — finished steps are skipped. Still stuck? Try the\n' >&2
    printf '     JupyterHub backup notebook, or ask an instructor.\n' >&2
    exit 1
}
trap 'printf "\n\n  Interrupted. Re-run the script to pick up where it left off.\n"; exit 130' INT

have() { command -v "$1" >/dev/null 2>&1; }

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
sh_quote()    { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

# curl with the token in a header, fed through stdin so it never shows up in `ps`.
# usage: curl_auth <Authorization|x-api-key> <curl args...>
curl_auth() {
    local header="$1" value; shift
    value="$(json_escape "$TOKEN")"
    [ "$header" = "Authorization" ] && value="Bearer $value"
    printf 'header = "%s: %s"\n' "$header" "$value" | curl -K - "$@"
}

# ---------------------------------------------------------------------------
# 0. Preflight
# ---------------------------------------------------------------------------
step "Checking this machine"

OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
    Darwin) PLATFORM="macOS" ;;
    Linux)  PLATFORM="Linux"
            if grep -qi microsoft /proc/version 2>/dev/null; then PLATFORM="Linux (WSL)"; fi ;;
    MINGW*|MSYS*|CYGWIN*)
        die "This looks like Git Bash / MSYS on Windows, which this script does not support." \
            "Use jfc_setup.ps1 from PowerShell instead, or run this script inside WSL." ;;
    *)  die "Unsupported operating system: $OS" "Claude Code runs on macOS, Linux, WSL and Windows." ;;
esac
case "$ARCH" in
    x86_64|amd64|arm64|aarch64) ;;
    *) die "Unsupported CPU architecture: $ARCH" "Claude Code needs an x86_64 or ARM64 machine." ;;
esac
ok "$PLATFORM on $ARCH"

missing=""
for tool in curl tar gzip; do have "$tool" || missing="$missing $tool"; done
if [ -n "$missing" ]; then
    hint="Install them with your package manager"
    have apt-get && hint="sudo apt-get install -y$missing"
    have dnf     && hint="sudo dnf install -y$missing"
    die "Missing required tools:$missing" "$hint"
fi
ok "curl, tar and gzip available"

case "$PLATFORM" in
    *WSL*) case "$WORK" in /mnt/*)
        warn "$WORK is on the Windows filesystem, which is very slow from WSL."
        note "Consider:  JFC_WORK=~/jfc-exercise bash jfc_setup.sh" ;;
    esac ;;
esac

# Git is optional — without it we download GitHub tarballs instead. On macOS,
# /usr/bin/git is only a stub until the Xcode Command Line Tools are installed,
# and calling it pops up an installer dialog, so check for that first.
HAVE_GIT=0
if have git; then
    if [ "$OS" = "Darwin" ] && [ "$(command -v git)" = "/usr/bin/git" ] && ! xcode-select -p >/dev/null 2>&1; then
        HAVE_GIT=0
    elif git --version >/dev/null 2>&1; then
        HAVE_GIT=1
    fi
fi
[ "$HAVE_GIT" = 1 ] && ok "git available" || note "git not available — will download repository snapshots instead"

# Memory and cores are advisory: the agent itself is light, the analysis code it writes is not.
if [ "$OS" = "Darwin" ]; then
    mem_gb=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
    cores=$(sysctl -n hw.ncpu 2>/dev/null || echo 0)
else
    mem_gb=$(( $(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0) / 1048576 ))
    cores=$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 0)
fi
if [ "$mem_gb" -gt 0 ] && [ "$mem_gb" -lt 7 ]; then
    warn "Only ~${mem_gb} GB of RAM — the lesson recommends 8 GB. It may still work; watch for OOM kills."
else
    ok "~${mem_gb} GB RAM, ${cores} CPU cores"
fi

mkdir -p "$WORK" || die "Could not create $WORK"
if [ ! -d "$WORK/data" ]; then
    free_kb=$(df -Pk "$WORK" 2>/dev/null | awk 'NR==2 {print $4}')
    need_kb=$(( 2500 * 1024 ))           # tarball + extracted samples coexist briefly
    if [ -n "$free_kb" ] && [ "$free_kb" -lt "$need_kb" ]; then
        die "Not enough free disk space in $WORK: $(( free_kb / 1024 )) MiB free, ~2500 MiB needed." \
            "Free some space, or choose another location:  JFC_WORK=/path/with/space bash jfc_setup.sh"
    fi
    [ -n "$free_kb" ] && ok "$(( free_kb / 1024 )) MiB free in $WORK"
fi

# ---------------------------------------------------------------------------
# 1. NRP token
# ---------------------------------------------------------------------------
step "Your NRP LLM token"

TOKEN="" ; TOKEN_SOURCE=""
if [ -n "${NRP_LLM_TOKEN:-}" ]; then
    TOKEN="$NRP_LLM_TOKEN"; TOKEN_SOURCE="\$NRP_LLM_TOKEN"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
    TOKEN="$OPENAI_API_KEY"; TOKEN_SOURCE="\$OPENAI_API_KEY"
elif [ -f "$ENV_FILE" ]; then
    TOKEN="$( . "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${OPENAI_API_KEY:-}" )"
    [ -n "$TOKEN" ] && TOKEN_SOURCE="$ENV_FILE (previous run)"
fi

# Where to read answers from: the terminal, even when the script arrives via `curl | bash`.
TTY=""
if [ "$ASSUME_YES" = 1 ]; then TTY=""
elif [ -t 0 ]; then TTY=/dev/stdin
elif (exec </dev/tty) 2>/dev/null; then TTY=/dev/tty
fi

ask_token() {
    [ -n "$TTY" ] || die "No token found and no terminal to ask for one." \
                         "Set it first:  export NRP_LLM_TOKEN=\"<your-token>\""
    printf '  Paste your token from https://nrp.ai/llmtoken (input is hidden): '
    IFS= read -rs TOKEN < "$TTY"
    printf '\n'
    TOKEN_SOURCE="prompt"
}

if [ -z "$TOKEN" ]; then
    ask_token
elif [ -n "$TTY" ]; then
    case "$TOKEN" in sk-*) warn "The token in $TOKEN_SOURCE starts with 'sk-' — that looks like an OpenAI key, not an NRP token." ;; esac
    printf '  Found a token in %s (%s…). Use it? [Y/n] ' "$TOKEN_SOURCE" "${TOKEN:0:6}"
    IFS= read -r reply < "$TTY"
    case "$reply" in [nN]*) ask_token ;; esac
fi

# Tidy up common paste accidents: whitespace, surrounding quotes, "Bearer ".
TOKEN="$(printf '%s' "$TOKEN" | tr -d '[:space:]')"
TOKEN="${TOKEN#Bearer}"; TOKEN="${TOKEN#\"}"; TOKEN="${TOKEN%\"}"; TOKEN="${TOKEN#\'}"; TOKEN="${TOKEN%\'}"
[ -n "$TOKEN" ] || die "The token is empty."
case "$TOKEN" in "<"*">") die "That is the placeholder, not a token." "Get yours at https://nrp.ai/llmtoken" ;; esac

# /v1/models answers even without a token, so check with a one-token chat request instead.
code=$(curl_auth "Authorization" -s -o /dev/null -w '%{http_code}' --max-time 60 \
    -X POST "$NRP_URL/v1/chat/completions" -H "content-type: application/json" \
    -d '{"model":"gemma-small","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}')
case "$code" in
    200)     ok "Token accepted by $NRP_URL" ;;
    401|403) die "NRP rejected the token (HTTP $code)." \
                 "Get a fresh one at https://nrp.ai/llmtoken, and make sure your account is in a" \
                 "namespace with LLM access (see the Setup page)." ;;
    000)     die "Could not reach $NRP_URL." "Check your internet connection, VPN or proxy." ;;
    *)       warn "Unexpected answer from $NRP_URL (HTTP $code) — continuing, but the agent may not work." ;;
esac

# ---------------------------------------------------------------------------
# 2. Claude Code and Pixi
# ---------------------------------------------------------------------------
step "Installing Claude Code and Pixi"

if have claude; then
    ok "Claude Code already installed: $(claude --version 2>/dev/null | head -1) — leaving it as is"
else
    note "Running the official installer (https://claude.ai/install.sh)…"
    curl -fsSL https://claude.ai/install.sh | bash \
        || die "The Claude Code installer failed." "See https://code.claude.com/docs/en/troubleshoot-install"
    hash -r
    have claude || die "Claude Code installed, but 'claude' is not in ~/.local/bin as expected."
    ok "Claude Code installed: $(claude --version 2>/dev/null | head -1)"
fi
if ! claude --help 2>/dev/null | grep -q '"auto"'; then
    warn "This Claude Code is too old for --permission-mode auto. Update it with:  claude update"
fi

if have pixi; then
    ok "Pixi already installed: $(pixi --version 2>/dev/null) — leaving it as is"
else
    note "Running the official installer (https://pixi.sh/install.sh), without touching your shell rc files…"
    curl -fsSL https://pixi.sh/install.sh | PIXI_NO_PATH_UPDATE=1 sh \
        || die "The Pixi installer failed." "See https://pixi.sh/latest/installation/"
    hash -r
    have pixi || die "Pixi installed, but 'pixi' is not in ~/.pixi/bin as expected."
    ok "Pixi installed: $(pixi --version 2>/dev/null)"
fi

# ---------------------------------------------------------------------------
# 3. Workshop-only Claude Code config + env file
# ---------------------------------------------------------------------------
step "Pointing Claude Code at NRP (in $CLAUDE_CFG — your ~/.claude is not touched)"

# Claude Code reads its user settings from $CLAUDE_CONFIG_DIR when that is set,
# so this file only applies to terminals that source nrp-env.sh. Rewriting it on
# a re-run is harmless: it is ours, not the user's.
mkdir -p "$CLAUDE_CFG" || die "Could not create $CLAUDE_CFG"
(
    umask 077
    cat > "$CLAUDE_CFG/settings.json.tmp" <<EOF
{
  "env": {
    "ANTHROPIC_BASE_URL": "$NRP_URL/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "$(json_escape "$TOKEN")",
    "ANTHROPIC_MODEL": "$MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL": "$MODEL",
    "ENABLE_TOOL_SEARCH": "false",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "$CONTEXT",
    "CLAUDE_CODE_EFFORT_LEVEL": "max",
    "CLAUDE_STREAM_IDLE_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
    "DISABLE_TELEMETRY": "1",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_MAX_RETRIES": "10"
  },
  "permissions": {
    "deny": ["WebSearch"]
  }
}
EOF
    mv -f "$CLAUDE_CFG/settings.json.tmp" "$CLAUDE_CFG/settings.json"
    cat > "$ENV_FILE.tmp" <<EOF
# NRP settings for the CLARIPHY JFC exercise (written by jfc_setup.sh).
# Load them into a terminal with:   source $(sh_quote "$ENV_FILE")
# This only affects the terminal you source it in. Note that 'claude' in that
# terminal uses the NRP config below, not your usual ~/.claude.
export OPENAI_API_BASE=$(sh_quote "$NRP_URL/v1")
export OPENAI_API_KEY=$(sh_quote "$TOKEN")
export WORK=$(sh_quote "$WORK")
export ROGUE=$(sh_quote "$ROGUE")
export CLAUDE_CONFIG_DIR=$(sh_quote "$CLAUDE_CFG")
export PATH="\$HOME/.local/bin:\$HOME/.pixi/bin:\$PATH"
EOF
    mv -f "$ENV_FILE.tmp" "$ENV_FILE"
) || die "Could not write the config files under $WORK"
ok "Claude Code config: $CLAUDE_CFG/settings.json (model: $MODEL)"
ok "Terminal settings:  $ENV_FILE"

note "Checking that $MODEL answers through the Anthropic-compatible endpoint…"
resp=$(curl_auth "x-api-key" -s --max-time 180 -w '\nHTTP_CODE=%{http_code}' \
    -X POST "$NRP_URL/anthropic/v1/messages" \
    -H "anthropic-version: 2023-06-01" -H "content-type: application/json" \
    -d "{\"model\":\"$(json_escape "$MODEL")\",\"max_tokens\":1000,\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: NRP OK\"}]}")
code="${resp##*HTTP_CODE=}"
if [ "$code" = 200 ] && printf '%s' "$resp" | grep -q '"type" *: *"text"'; then
    ok "$MODEL replied through $NRP_URL/anthropic"
elif [ "$code" = 200 ]; then
    warn "$MODEL answered but returned no text (probably spent its budget reasoning) — usually fine."
else
    warn "The Anthropic-compatible endpoint answered HTTP $code for model $MODEL."
    note "The agent may not start. Try another model:  NRP_MODEL=glm-5 bash jfc_setup.sh"
    note "Current model status: https://nrp.ai/llm-status/"
fi

# ---------------------------------------------------------------------------
# 4. Repositories
# ---------------------------------------------------------------------------
step "Getting the JFC framework and the H→4ℓ tutorial context"

# usage: fetch_repo <dir-name> <github owner/repo> <branch>
fetch_repo() {
    local name="$1" repo="$2" branch="$3" dest="$WORK/$1" tmp="$WORK/.$1.partial"
    if [ -d "$dest" ] && [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
        ok "$name already present — leaving it as is"
        return
    fi
    rm -rf "$tmp"
    if [ "$HAVE_GIT" = 1 ]; then
        git clone -q --depth 1 -b "$branch" "https://github.com/$repo.git" "$tmp" \
            || { rm -rf "$tmp"; die "git clone of $repo failed." "Check your connection and re-run."; }
    else
        mkdir -p "$tmp"
        curl -fsSL --retry 3 "https://codeload.github.com/$repo/tar.gz/refs/heads/$branch" \
            | tar -xzf - -C "$tmp" --strip-components=1 \
            || { rm -rf "$tmp"; die "Downloading $repo failed." "Check your connection and re-run."; }
    fi
    rm -rf "$dest" && mv "$tmp" "$dest"
    ok "$name ($repo, branch $branch)"
}
fetch_repo h4l_agent_test violatingcp/h4l_agent_test main
fetch_repo jfc            violatingcp/jfc            jfc_lite

# ---------------------------------------------------------------------------
# 5. CMS Open Data samples
# ---------------------------------------------------------------------------
step "Getting the CMS Open Data samples (~860 MiB)"

if [ -d "$WORK/data" ] && [ -n "$(ls -A "$WORK/data" 2>/dev/null)" ]; then
    ok "data/ already present — skipping download ($(du -sh "$WORK/data" 2>/dev/null | cut -f1))"
else
    tgz="$WORK/data.tgz"; part="$tgz.part"
    expected=$(curl -sIL --max-time 30 "$DATA_URL" | tr -d '\r' \
               | awk 'tolower($1)=="content-length:" {n=$2} END {print n}')
    size_of() { wc -c < "$1" 2>/dev/null | tr -d ' '; }

    if [ -f "$tgz" ] && { [ -z "$expected" ] || [ "$(size_of "$tgz")" = "$expected" ]; }; then
        ok "data.tgz already downloaded"
    else
        if [ -f "$part" ] && [ -n "$expected" ] && [ "$(size_of "$part")" = "$expected" ]; then
            note "Previous download was already complete."
        else
            [ -f "$part" ] && note "Resuming the previous download…" || note "Downloading — a few minutes on a good connection…"
            if [ -t 2 ]; then progress="--progress-bar"; else progress="-sS"; fi
            curl -fL -C - --retry 5 --retry-delay 5 $progress -o "$part" "$DATA_URL" \
                || die "The download stopped." "Re-run the script to resume it."
        fi
        if [ -n "$expected" ] && [ "$(size_of "$part")" != "$expected" ]; then
            die "Downloaded $(size_of "$part") bytes, expected $expected." "Re-run the script to resume it."
        fi
        mv -f "$part" "$tgz"
        ok "Downloaded data.tgz"
    fi

    # Extract next to the final location, then move it into place, so a failed or
    # interrupted extraction never leaves a half-filled data/ that looks finished.
    note "Extracting…"
    ext="$WORK/.data-extract"
    rm -rf "$ext" && mkdir -p "$ext"
    if ! tar -xzf "$tgz" -C "$ext" 2> "$WORK/.tar-errors.log"; then
        rm -rf "$ext"
        tail -5 "$WORK/.tar-errors.log" >&2
        rm -f "$tgz"
        die "Extracting data.tgz failed (corrupt download, or the disk filled up)." \
            "The tarball was removed; re-run the script to download it again."
    fi
    rm -f "$WORK/.tar-errors.log"
    if [ -d "$ext/data" ]; then mv "$ext/data" "$WORK/data"; rm -rf "$ext"; else mv "$ext" "$WORK/data"; fi
    rm -f "$tgz"
    ok "Samples extracted to $WORK/data ($(du -sh "$WORK/data" 2>/dev/null | cut -f1))"
fi

# ---------------------------------------------------------------------------
# 6. Stage the fast-path analysis
# ---------------------------------------------------------------------------
step "Staging the fast-path analysis in $ROGUE"

mkdir -p "$ROGUE" || die "Could not create $ROGUE"
# Only add what is missing, so a re-run never overwrites anything the agent changed.
if [ -L "$ROGUE/data" ] || [ ! -e "$ROGUE/data" ]; then
    ln -sfn "$WORK/data" "$ROGUE/data"
fi
for item in prompt.md h4l_ntuplize.py docs .claude; do
    if [ ! -e "$ROGUE/$item" ]; then
        cp -R "$WORK/h4l_agent_test/$item" "$ROGUE/" || die "Could not copy $item into $ROGUE"
    fi
done
ok "prompt.md, docs/, h4l_ntuplize.py, .claude/ and a data/ link are in place"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
cat <<EOF

${BOLD}==> All set.${RESET} Launch the agent (Step 2 of the lesson) in a fresh terminal:

    source $(sh_quote "$ENV_FILE")
    cd "\$ROGUE"
    cat prompt.md | claude --permission-mode auto

Then leave it running and carry on with the tutorial. To watch its progress
from a second terminal, source the same file and look inside \$ROGUE.

Your own Claude Code settings (~/.claude) and shell startup files were not
modified. To remove everything after the workshop:  rm -rf $(sh_quote "$WORK")
EOF
