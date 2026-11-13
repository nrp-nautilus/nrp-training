"""Small drawing kit for the deck, on top of python-pptx and the SDSC template.

Copied from the SDSC HPC-CI webinar deck (Oct 2026); body font switched to Source Sans Pro,
which PowerPoint for Mac ships as a cloud font.

The look follows the NRP 7GRP deck built on the same template: Teko titles (from the
master), Source Sans 3 body, navy / SDSC blue / gold, rounded cards, icons in circles,
Teko stat numbers, navy code panels in Courier New. Everything is drawn as native,
editable shapes; only plots and screenshots are pictures.
"""
import copy
import re
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
ICONS = HERE / "assets" / "icons"

# ── palette and type ────────────────────────────────────────────────────────────────
NAVY, BLUE, GOLD = "182B49", "00629B", "FFCD00"
CARD, CARD2, CARD_DARK = "EEF3F8", "DDE8F2", "22385C"
BODY, MUTED, LIGHT, WHITE = "2B3648", "5C6778", "C9D4E3", "FFFFFF"
CODE_BG, CODE_TXT, CODE_CMT, CODE_STR = "182B49", "FFFFFF", "9FB3CC", "FFCD00"
GREEN, ORANGE = "1BAF7A", "EB6834"
SANS, SANS_SB, SANS_BLACK, TEKO, MONO = "Source Sans Pro", "Source Sans Pro SemiBold", "Source Sans Pro Black", "Teko SemiBold", "Courier New"

SLIDE_W, SLIDE_H = 13.333, 7.5
X0, X1 = 0.60, 12.73            # content left / right edge
Y0, Y1 = 1.72, 6.72             # content top (below subtitle) / bottom (above footer bar)


CODE_WARNINGS = []
CODE_SIZES = []
ICONS_USED = set()


def rgb(h):
    return RGBColor.from_string(h)


# ── inline markup: **bold**, `mono`, [[accent]] ─────────────────────────────────────
TOKEN = re.compile(r"(\*\*.+?\*\*|`.+?`|\[\[.+?\]\])")


def runs_of(text):
    out = []
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**"):
            out.append((part[2:-2], {"bold": True}))
        elif part.startswith("`"):
            out.append((part[1:-1], {"mono": True}))
        elif part.startswith("[["):
            out.append((part[2:-2], {"accent": True}))
        else:
            out.append((part, {}))
    return out


class P:
    """One paragraph: text with inline markup plus paragraph-level style."""

    def __init__(self, text, size=16, color=BODY, bold=False, font=SANS, before=0, after=0,
                 line=1.0, align=None, bullet=False, accent=BLUE, italic=False, level=0):
        self.__dict__.update(locals())
        del self.__dict__["self"]


def _set_bullet(p, char="•", color=BLUE, indent=0.22, level=0):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(indent * (level + 1)))))
    pPr.set("indent", str(int(-Inches(indent))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum", "a:buClr", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    buClr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(buClr, qn("a:srgbClr")).set("val", color)
    buFont = etree.SubElement(pPr, qn("a:buFont"))
    buFont.set("typeface", "Arial")
    buChar = etree.SubElement(pPr, qn("a:buChar"))
    buChar.set("char", char)


def _no_bullet(p):
    pPr = p._p.get_or_add_pPr()
    if pPr.find(qn("a:buNone")) is None:
        etree.SubElement(pPr, qn("a:buNone"))


def fill_tf(tf, paras, anchor="t", wrap=True, margin=0.0):
    tf.word_wrap = wrap
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(margin))
    if isinstance(paras, (str, P)):
        paras = [paras]
    expanded = []
    for para in paras:
        if isinstance(para, P) and "\n" in para.text:
            for k, part in enumerate(para.text.split("\n")):
                q = P(**{**para.__dict__, "text": part, "before": para.before if k == 0 else 0})
                expanded.append(q)
        else:
            expanded.append(para)
    paras = expanded
    first = True
    for para in paras:
        if isinstance(para, str):
            para = P(para)
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        if para.align:
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[para.align]
        p.line_spacing = para.line
        p.space_before = Pt(para.before)
        p.space_after = Pt(para.after)
        if para.bullet:
            _set_bullet(p, color=para.accent, level=para.level)
        else:
            _no_bullet(p)
        for text, st in runs_of(para.text):
            r = p.add_run()
            r.text = text
            f = r.font
            f.size = Pt(para.size)
            f.bold = para.bold or st.get("bold", False)
            f.italic = para.italic
            f.name = MONO if st.get("mono") else para.font
            f.color.rgb = rgb(para.accent if st.get("accent") else para.color)
    return tf


class SlideW:
    def __init__(self, deck, slide, dark=False):
        self.deck, self.s, self.dark = deck, slide, dark

    # primitives ---------------------------------------------------------------------
    def rect(self, x, y, w, h, fill=CARD, radius=0.04, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name=None):
        sh = self.s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            sh.adjustments[0] = radius
        if fill:
            sh.fill.solid()
            sh.fill.fore_color.rgb = rgb(fill)
        else:
            sh.fill.background()
        if line:
            sh.line.color.rgb = rgb(line)
            sh.line.width = Pt(1.25)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        if name:
            sh.name = name
        return sh

    def text(self, x, y, w, h, paras, anchor="t", wrap=True, margin=0.0, name=None):
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        fill_tf(tb.text_frame, paras, anchor=anchor, wrap=wrap, margin=margin)
        if name:
            tb.name = name
        return tb

    def card(self, x, y, w, h, fill=None, radius=0.04, line=None):
        return self.rect(x, y, w, h, fill=fill or (CARD_DARK if self.dark else CARD), radius=radius, line=line)

    def icon(self, name, x, y, d=0.52, bg=BLUE, fg="white", pad=0.2):
        if bg:
            c = self.s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
            c.fill.solid(); c.fill.fore_color.rgb = rgb(bg); c.line.fill.background(); c.shadow.inherit = False
        inset = d * pad
        ICONS_USED.add((name, fg))
        return self.s.shapes.add_picture(str(ICONS / f"Pi{name}Fill_{fg}.png"), Inches(x + inset),
                                         Inches(y + inset), Inches(d - 2 * inset), Inches(d - 2 * inset))

    def image(self, path, x, y, w, h, align="c", valign="m", border=None):
        """Place a picture inside the box (x, y, w, h), keeping its aspect ratio."""
        from PIL import Image
        iw, ih = Image.open(path).size
        scale = min(w / iw, h / ih)
        pw, ph = iw * scale, ih * scale
        px = x + {"l": 0, "c": (w - pw) / 2, "r": w - pw}[align]
        py = y + {"t": 0, "m": (h - ph) / 2, "b": h - ph}[valign]
        pic = self.s.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))
        if border:
            pic.line.color.rgb = rgb(border)
            pic.line.width = Pt(1)
        return pic

    def link(self, x, y, w, h, url, text=None, size=14, align="l"):
        """A clickable, underlined URL, the way links appear on hand-made slides."""
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        for side in ("left", "right", "top", "bottom"):
            setattr(tf, f"margin_{side}", 0)
        p = tf.paragraphs[0]
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        r = p.add_run()
        r.text = text or url
        r.font.size = Pt(size); r.font.name = SANS; r.font.underline = True
        r.font.color.rgb = rgb(BLUE)
        r.hyperlink.address = url if url.startswith("http") else "https://" + url
        return tb

    def line(self, x1, y1, x2, y2, color=MUTED, width=1.5, arrow=True, dash=False):
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = rgb(color)
        c.line.width = Pt(width)
        ln = c.line._get_or_add_ln()
        if dash:
            pd_ = etree.SubElement(ln, qn("a:prstDash")); pd_.set("val", "dash")
        if arrow:
            tail = etree.SubElement(ln, qn("a:tailEnd"))
            tail.set("type", "triangle"); tail.set("w", "med"); tail.set("len", "med")
        return c

    def arrow_right(self, x, y, w=0.34, h=0.34, color=MUTED):
        a = self.s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
        a.fill.solid(); a.fill.fore_color.rgb = rgb(color); a.line.fill.background(); a.shadow.inherit = False
        return a

    def arrow_down(self, x, y, w=0.34, h=0.3, color=MUTED):
        a = self.s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
        a.fill.solid(); a.fill.fore_color.rgb = rgb(color); a.line.fill.background(); a.shadow.inherit = False
        return a

    # composites ---------------------------------------------------------------------
    def pill(self, x, y, w, h, text, fill=BLUE, color=WHITE, size=13, bold=True, font=SANS):
        sh = self.rect(x, y, w, h, fill=fill, radius=0.5)
        fill_tf(sh.text_frame, P(text, size=size, color=color, bold=bold, align="c", font=font), anchor="m",
                margin=0.04)
        return sh

    def icon_card(self, x, y, w, h, icon, head, body, head_size=18, body_size=15, fill=None, icon_bg=BLUE,
                  d=0.56, body_color=None, stack=False):
        """A card with an icon and ONE text box holding the heading and the body, so a heading that
        wraps pushes the body down instead of overlapping it (PowerPoint wraps differently from
        LibreOffice). stack=True puts the text under the icon instead of beside it."""
        self.card(x, y, w, h, fill=fill)
        pad = 0.22
        self.icon(icon, x + pad, y + pad, d=d, bg=icon_bg)
        hc = WHITE if self.dark else NAVY
        bc = body_color or (LIGHT if self.dark else BODY)
        paras = [P(head, size=head_size, bold=True, color=hc, line=0.95)]
        paras += body if isinstance(body, list) else [P(body, size=body_size, color=bc, line=1.0, before=4)]
        if stack:
            self.text(x + pad, y + pad + d + 0.12, w - 2 * pad, h - d - 2 * pad - 0.12, paras)
        else:
            tx = x + pad + d + 0.18
            ty = y + pad + max(0.0, (d - head_size * 1.2 / 72) / 2) - 0.03
            self.text(tx, ty, x + w - pad - tx, y + h - pad - ty, paras)

    def stat(self, x, y, w, big, label, big_size=44, label_size=15, color=None, label_color=None, h=None):
        c = color or (GOLD if self.dark else BLUE)
        lc = label_color or (LIGHT if self.dark else BODY)
        return self.text(x, y, w, h or 1.2, [P(big, size=big_size, color=c, font=TEKO, line=0.8),
                                             P(label, size=label_size, color=lc, line=0.98, before=2)])

    def step(self, x, y, w, h, n, head, body, fill=CARD2):
        self.card(x, y, w, h, fill=fill)
        self.text(x + 0.2, y + 0.08, 0.7, 0.8, P(str(n), size=40, font=TEKO, color=BLUE))
        self.text(x + 0.2, y + 0.72, w - 0.36, h - 0.8,
                  [P(head, size=17, bold=True, color=NAVY, line=0.95), P(body, size=14, color=BODY, before=3)])

    def code(self, x, y, w, h, code, size=13, fill=CODE_BG, title=None, lang=None, min_size=11):
        # Courier New advances 0.6 em; keep every line on one row and the block inside the panel.
        lines_ = code.strip("\n").split("\n")
        longest = max(len(l) for l in lines_)
        while size > min_size and (longest * size * 0.6 / 72 > (w - 0.5) * 0.97 or
                                   len(lines_) * size * 1.08 * 1.17 / 72 + 0.4 > h):
            size -= 0.5
        if longest * size * 0.6 / 72 > (w - 0.5) * 0.97 or len(lines_) * size * 1.08 * 1.17 / 72 + 0.4 > h:
            CODE_WARNINGS.append(f"code panel too small ({longest} chars x {len(lines_)} lines at {size}pt in "
                                 f"{w:.2f}x{h:.2f}in): {lines_[0][:40]!r}")
        CODE_SIZES.append((size, longest, len(lines_), lines_[0][:40]))
        sh = self.rect(x, y, w, h, fill=fill, radius=0.03)
        tf = sh.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.TOP
        for side in ("left", "right", "top", "bottom"):
            setattr(tf, f"margin_{side}", Inches(0.18))
        lines = code.strip("\n").split("\n")
        first = True
        if title:
            p = tf.paragraphs[0]; first = False
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run(); r.text = title
            r.font.size = Pt(size - 1); r.font.name = SANS_SB; r.font.color.rgb = rgb(GOLD); r.font.italic = False
            p.space_after = Pt(4)
        for ln in lines:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.line_spacing = 1.08
            p.alignment = PP_ALIGN.LEFT
            stripped = ln.lstrip()
            if stripped.startswith(("#", "//")) and not stripped.startswith("#!"):
                segs = [(ln, CODE_CMT)]
            else:
                segs = []
                # split off trailing comment ("  # ...")
                m = re.search(r"\s(#|//)\s", ln)
                body, cmt = (ln[:m.start()], ln[m.start():]) if m and lang != "yaml" else (ln, "")
                for part in re.split(r'("[^"]*"|\'[^\']*\')', body):
                    if not part:
                        continue
                    segs.append((part, CODE_STR if part[:1] in "\"'" else CODE_TXT))
                if cmt:
                    segs.append((cmt, CODE_CMT))
            if not segs or ln == "":
                segs = [(" ", CODE_TXT)]
            for t, col in segs:
                r = p.add_run(); r.text = t
                r.font.size = Pt(size); r.font.name = MONO; r.font.color.rgb = rgb(col); r.font.bold = False
                r.font.italic = False
        return sh

    def table(self, x, y, w, col_w, rows, size=14, head_size=14, row_h=0.38, head_fill=NAVY, zebra=True,
              col_align=None, bold_first=True, mono_cols=()):
        nr, nc = len(rows), len(rows[0])
        gt = self.s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(row_h * nr))
        tbl = gt.table
        # plain style: remove banding from the default table style
        tblPr = tbl._tbl.tblPr
        tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
        tot = sum(col_w)
        for j, cw in enumerate(col_w):
            tbl.columns[j].width = Inches(w * cw / tot)
        for i, row in enumerate(rows):
            tbl.rows[i].height = Inches(row_h)
            for j, val in enumerate(row):
                cell = tbl.cell(i, j)
                cell.margin_left = cell.margin_right = Inches(0.08)
                cell.margin_top = cell.margin_bottom = Inches(0.03)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                head = i == 0
                fillc = head_fill if head else ((CARD if i % 2 == 0 else WHITE) if zebra else WHITE)
                cell.fill.solid(); cell.fill.fore_color.rgb = rgb(fillc)
                al = (col_align[j] if col_align else "l")
                para = P(str(val), size=head_size if head else size, color=WHITE if head else BODY,
                         bold=head or (bold_first and j == 0), align=al,
                         font=MONO if (j in mono_cols and not head) else SANS, line=0.95)
                tf = cell.text_frame
                for p in list(tf.paragraphs)[1:]:
                    p._p.getparent().remove(p._p)
                tf.paragraphs[0].text = ""
                fill_tf(tf, para, anchor="m")
        return gt

    def notes(self, text):
        # strip per-line indentation so notes written inside functions read the same
        self.s.notes_slide.notes_text_frame.text = "\n".join(l.strip() for l in text.strip().splitlines())


class Deck:
    def __init__(self, template, footer="NRP"):
        self.p = Presentation(str(template))
        # Start empty even if the template file has slides in it (e.g. a starter title slide).
        sld_ids = self.p.slides._sldIdLst
        for sid in list(sld_ids):
            self.p.part.drop_rel(sid.rId)
            sld_ids.remove(sid)
        self.footer = footer
        self.layouts = {l.name: l for l in self.p.slide_layouts}
        self.n = 0          # the number printed in the footer; build copies of a slide repeat it

    def _footer(self, s, label, dark=False):
        """The slide number as plain text, so build copies of one slide (fake animations,
        paged in a PDF) all show the same number. The section is kept in the shape name."""
        tb = s.shapes.add_textbox(Inches(6.0), Inches(7.02), Inches(5.25), Inches(0.40))
        tb.name = f"Footer {label}"
        tf = tb.text_frame
        tf.word_wrap = False
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for side in ("left", "right", "top", "bottom"):
            setattr(tf, f"margin_{side}", 0)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run(); r.text = str(self.n)
        r.font.size = Pt(11); r.font.italic = False; r.font.name = SANS_SB
        r.font.color.rgb = rgb(WHITE)

    def slide(self, title=None, subtitle=None, section="", layout="Title Only", dark=None, title_size=None,
              cont=False):
        """cont=True: a build copy of the previous slide; it keeps that slide's number."""
        if not cont:
            self.n += 1
        lay = self.layouts[layout]
        s = self.p.slides.add_slide(lay)
        dark = ("Reverse" in layout) if dark is None else dark
        w = SlideW(self, s, dark=dark)
        if title is not None and s.shapes.title is not None:
            t = s.shapes.title
            t.left, t.top, t.width, t.height = Inches(0.50), Inches(0.26), Inches(12.33), Inches(0.90)
            tf = t.text_frame
            tf.text = ""
            r = tf.paragraphs[0].add_run(); r.text = title
            n = len(title)
            # sized so the title stays on one line even when Teko is missing and a wider font stands in
            r.font.size = Pt(title_size or (40 if n <= 35 else 36 if n <= 39 else 32 if n <= 43 else 28))
            r.font.italic = False
            tf.paragraphs[0].line_spacing = 0.85
        if subtitle:
            w.text(0.60, 1.14, 12.10, 0.42, P(subtitle, size=18, color=LIGHT if dark else MUTED), name="Subtitle")
        if section is not None:
            self._footer(s, section, dark)
        return w

    def save(self, path):
        self.p.save(str(path))
