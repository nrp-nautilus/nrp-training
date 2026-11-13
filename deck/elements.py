"""Slide elements that render twice: as HTML for the animated deck, and as shapes in the PowerPoint.

Each slide in slides.py is a list of these, placed in inches on the 13.333 x 7.5 in slide. Three
attributes drive the animation:

    step=k      shown from build step k on (HTML: data-s)
    only=[k..]  shown only at those steps (HTML: data-only)
    hl=[k..]    highlighted at those steps: a box turns navy, an arrow blue (HTML: data-hl)

The PowerPoint shows a slide in its final state, or, for slides marked builds=True, one copy per step
(a fake animation, paged through in the PDF) with the same slide number.
"""
import base64
import re
from html import escape
from pathlib import Path

from deckkit import (BLUE, BODY, CARD, GOLD, LIGHT, MONO, MUTED, NAVY, ORANGE, SANS, WHITE, P)

PX = 144                                   # pixels per inch on the 1920 x 1080 stage; 1 pt = 2 px
DIM_FILL, DIM_TEXT, DIM_SUB, DIM_LINE = "F3F4F6", "A3ABB6", "B9C0C9", "D5DAE0"
GREEN, RED, AMBER = "1B7F55", "B3261E", "C27C0E"


def uri(path):
    ext = Path(path).suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}[ext]
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def md(t):
    """**bold**, `code` and [[accent]] in HTML."""
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[\[(.+?)\]\]", r'<span class="acc">\1</span>', t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


def pos(x, y, w=None, h=None):
    s = f"left:{x * PX:.0f}px;top:{y * PX:.0f}px;"
    if w is not None:
        s += f"width:{w * PX:.0f}px;"
    if h is not None:
        s += f"height:{h * PX:.0f}px;"
    return s


def steps_attr(v):
    return " ".join(str(k) for k in ([v] if isinstance(v, int) else v))


class El:
    """Base: a box at (x, y, w, h) inches, with optional step / only / hl."""

    def __init__(self, x, y, w, h, step=None, only=None, hl=None, cls="", style="", pptx=True):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.step, self.only, self.hl, self.cls, self.style, self.in_pptx = step, only, hl, cls, style, pptx

    # visibility and highlight at a build step
    def visible(self, k):
        if self.step is not None and k < self.step:
            return False
        if self.only is not None and k not in ([self.only] if isinstance(self.only, int) else self.only):
            return False
        return True

    def lit(self, k):
        return self.hl is not None and k in ([self.hl] if isinstance(self.hl, int) else self.hl)

    def wrap(self, inner, extra_cls=""):
        a = f' data-s="{self.step}"' if self.step is not None else ""
        a += f' data-only="{steps_attr(self.only)}"' if self.only is not None else ""
        a += f' data-hl="{steps_attr(self.hl)}"' if self.hl is not None else ""
        return (f'<div class="a {self.cls} {extra_cls}"{a} style="{pos(self.x, self.y, self.w, self.h)}{self.style}">'
                f'{inner}</div>')

    def html(self):
        return self.wrap("")

    def pptx(self, s, k):
        pass


class T:
    """A paragraph for Text: the same fields as deckkit.P."""

    def __init__(self, text, size=20, color=BODY, bold=False, align="l", font=SANS, before=0, italic=False, line=1.04,
                 step=None):
        self.__dict__.update(locals())
        del self.__dict__["self"]

    def p(self):
        return P(self.text, size=self.size, color=self.color, bold=self.bold, align=self.align, font=self.font,
                 before=self.before, italic=self.italic, line=self.line)

    def html(self):
        st = (f"font-size:{self.size * 2}px;color:#{self.color};text-align:"
              f"{ {'l': 'left', 'c': 'center', 'r': 'right'}[self.align]};margin-top:{self.before * 2}px;"
              f"line-height:{max(self.line, 1.0) * 1.2:.2f};")
        if self.bold:
            st += "font-weight:700;"
        if self.italic:
            st += "font-style:italic;"
        if self.font == MONO:
            st += "font-family:var(--f-mono);"
        a = f' data-s="{self.step}"' if self.step is not None else ""
        return f'<p style="{st}"{a}>{md(self.text)}</p>'


class Text(El):
    def __init__(self, x, y, w, h, paras, anchor="t", **kw):
        super().__init__(x, y, w, h, **kw)
        self.paras = [paras] if isinstance(paras, (str, T)) else paras
        self.paras = [T(p) if isinstance(p, str) else p for p in self.paras]
        self.anchor = anchor

    def html(self):
        st = {"t": "", "m": "display:flex;flex-direction:column;justify-content:center;",
              "b": "display:flex;flex-direction:column;justify-content:flex-end;"}[self.anchor]
        return self.wrap(f'<div style="width:100%;height:100%;{st}">' + "".join(p.html() for p in self.paras)
                         + "</div>")

    def pptx(self, s, k):
        paras = [p.p() for p in self.paras if p.step is None or p.step <= k]
        if paras:
            s.text(self.x, self.y, self.w, self.h, paras, anchor=self.anchor)


class Bullets(El):
    """items: "text", (text, level) or (text, level, step)."""

    def __init__(self, x, y, w, h, items, size=20, gap=9, color=BODY, **kw):
        super().__init__(x, y, w, h, **kw)
        self.items = [(it, 0, None) if isinstance(it, str) else (tuple(it) + (None,))[:3] for it in items]
        self.size, self.gap, self.color = size, gap, color

    def html(self):
        li = ""
        for t, lvl, st in self.items:
            a = f' data-s="{st}"' if st is not None else ""
            li += f'<li class="l{lvl}"{a}>{md(t)}</li>'
        return self.wrap(f'<ul class="bl" style="font-size:{self.size * 2}px;--gap:{self.gap * 2.4:.0f}px;'
                         f'color:#{self.color}">{li}</ul>')

    def pptx(self, s, k):
        paras = []
        for t, lvl, st in self.items:
            if st is not None and st > k:
                continue
            paras.append(P(t, size=self.size if lvl == 0 else self.size - 3, color=self.color, bullet=True, level=lvl,
                           accent=NAVY if self.color == BODY else GOLD,
                           before=(self.gap if lvl == 0 else 3) if paras else 0, line=1.04))
        if paras:
            s.text(self.x, self.y, self.w, self.h, paras)


class Code(El):
    def __init__(self, x, y, w, h, text, size=13, title=None, lang=None, typed=False, lines_hl=None, **kw):
        """lines_hl: {line number (1-based): [steps]} highlights those lines at those steps (HTML)."""
        super().__init__(x, y, w, h, **kw)
        self.text, self.title, self.lang, self.typed = text.strip("\n"), title, lang, typed
        self.lines_hl = lines_hl or {}
        # shrink until every line fits on one row and the block fits the panel (deckkit's rule, for both outputs)
        lines = self.text.split("\n") + ([title] if title else [])
        longest = max(len(l) for l in self.text.split("\n"))
        while size > 9 and (longest * size * 0.6 / 72 > (w - 0.5) * 0.97 or
                            len(lines) * size * 1.08 * 1.17 / 72 + 0.45 > h):
            size -= 0.5
        self.size = size

    def html(self):
        lines = []
        for i, ln in enumerate(self.text.split("\n"), 1):
            e = escape(ln)
            if self.lang != "yaml" or ln.lstrip().startswith("#"):
                e = re.sub(r"(^\s*#.*$|\s#\s.*$)", r'<span class="cm">\1</span>', e)
            e = re.sub(r"(&quot;[^&]*?&quot;)", r'<span class="st">\1</span>', e)
            hl = self.lines_hl.get(i)
            a = f' data-hl="{steps_attr(hl)}"' if hl else ""
            lines.append(f'<span class="ln"{a} style="--i:{i}">{e or " "}</span>')
        t = f'<div class="ct">{escape(self.title)}</div>' if self.title else ""
        return self.wrap(f'<div class="code{" typed" if self.typed else ""}" style="font-size:{self.size * 2}px">{t}'
                         f'<pre>{"".join(lines)}</pre></div>')

    def pptx(self, s, k):
        s.code(self.x, self.y, self.w, self.h, self.text, size=self.size, title=self.title, lang=self.lang,
               min_size=9)


class Table(El):
    def __init__(self, x, y, w, h, rows, widths, size=15, mono=(), row_h=0.5, bold_first=True, **kw):
        super().__init__(x, y, w, h, **kw)
        self.rows, self.widths, self.size, self.mono, self.row_h, self.bold_first = (rows, widths, size, mono, row_h,
                                                                                    bold_first)

    def html(self):
        tot = sum(self.widths)
        cg = "".join(f'<col style="width:{w / tot * 100:.1f}%">' for w in self.widths)
        head = "".join(f"<th>{md(c)}</th>" for c in self.rows[0])
        body = ""
        for r in self.rows[1:]:
            body += "<tr>" + "".join(f'<td class="{"mono" if j in self.mono else ""}">{md(c)}</td>'
                                     for j, c in enumerate(r)) + "</tr>"
        bf = "" if self.bold_first else " nobold"
        return self.wrap(f'<table class="tb{bf}" style="font-size:{self.size * 2}px;--rh:{self.row_h * PX:.0f}px">'
                         f'<colgroup>{cg}</colgroup><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')

    def pptx(self, s, k):
        s.table(self.x, self.y, self.w, self.widths, self.rows, size=self.size, head_size=self.size,
                row_h=self.row_h, mono_cols=self.mono, bold_first=self.bold_first)


class Image(El):
    def __init__(self, x, y, w, h, path, border=None, align="c", valign="m", **kw):
        super().__init__(x, y, w, h, **kw)
        self.path, self.border, self.align, self.valign = path, border, align, valign

    def html(self):
        b = f"border:2px solid #{self.border};" if self.border else ""
        jc = {"l": "flex-start", "c": "center", "r": "flex-end"}[self.align]
        ai = {"t": "flex-start", "m": "center", "b": "flex-end"}[self.valign]
        return self.wrap(f'<div style="width:100%;height:100%;display:flex;justify-content:{jc};align-items:{ai}">'
                         f'<img class="im" src="{uri(self.path)}" style="{b}" alt=""></div>')

    def pptx(self, s, k):
        s.image(self.path, self.x, self.y, self.w, self.h, align=self.align, valign=self.valign, border=self.border)


BOX_STATES = {"normal": (CARD, NAVY, BODY, "C9D4E3"), "active": (NAVY, WHITE, LIGHT, None),
              "dim": (DIM_FILL, DIM_TEXT, DIM_SUB, "E3E6EA"), "white": (WHITE, NAVY, BODY, "B9C7D8"),
              "orange": ("FDEBE3", NAVY, BODY, ORANGE), "gold": ("FFF4CC", NAVY, BODY, "E9B55C"),
              "green": ("D3EEE1", NAVY, BODY, "7CC4A2"), "red": ("F6D6D3", NAVY, BODY, "D98C85")}


class Box(El):
    """A rounded box with a bold line and an optional second line; hl steps turn it navy."""

    def __init__(self, x, y, w, h, head, sub=None, state="normal", head_size=16, sub_size=12.5, mono_sub=False,
                 align="c", **kw):
        super().__init__(x, y, w, h, **kw)
        self.head, self.sub, self.state, self.hs, self.ss, self.mono_sub, self.align = (head, sub, state, head_size,
                                                                                        sub_size, mono_sub, align)

    def html(self):
        s = f'<span class="bs{" mono" if self.mono_sub else ""}" style="font-size:{self.ss * 2}px">{md(self.sub)}</span>' \
            if self.sub else ""
        al = {"c": "center", "l": "flex-start"}[self.align]
        return self.wrap(f'<div class="bx {self.state}" style="align-items:{al};text-align:'
                         f'{ {"c": "center", "l": "left"}[self.align]}"><span class="bh" style="font-size:'
                         f'{self.hs * 2}px">{md(self.head)}</span>{s}</div>')

    def pptx(self, s, k):
        st = "active" if self.lit(k) else self.state
        fill, hc, sc, line = BOX_STATES[st]
        sh = s.rect(self.x, self.y, self.w, self.h, fill=fill, radius=0.08, line=line)
        if st == "orange":
            from pptx.util import Pt
            sh.line.width = Pt(2.25)
        paras = [P(self.head, size=self.hs, bold=True, color=hc, align=self.align, line=0.95)]
        if self.sub:
            paras.append(P(self.sub, size=self.ss, color=sc, align=self.align, line=0.98, before=2,
                           font=MONO if self.mono_sub else SANS))
        s.text(self.x + 0.08, self.y, self.w - 0.16, self.h, paras, anchor="m")


class Frame(El):
    """A plain outlined (or filled) rectangle, for grouping; label on its top-left."""

    def __init__(self, x, y, w, h, label=None, fill=None, line="B9C7D8", dashed=False, label_color=NAVY,
                 label_size=15, radius=0.04, **kw):
        super().__init__(x, y, w, h, **kw)
        self.label, self.fill, self.line, self.dashed, self.lc, self.ls, self.radius = (label, fill, line, dashed,
                                                                                         label_color, label_size,
                                                                                         radius)

    def html(self):
        bg = f"background:#{self.fill};" if self.fill else ""
        bd = f"border:3px {'dashed' if self.dashed else 'solid'} #{self.line};" if self.line else ""
        lab = (f'<span class="fl" style="color:#{self.lc};font-size:{self.ls * 2}px">{md(self.label)}</span>'
               if self.label else "")
        return self.wrap(f'<div class="frame" style="{bg}{bd}border-radius:{self.radius * PX * 2:.0f}px">{lab}</div>')

    def pptx(self, s, k):
        sh = s.rect(self.x, self.y, self.w, self.h, fill=self.fill, radius=self.radius, line=self.line)
        if self.dashed and self.line:
            from lxml import etree
            from pptx.oxml.ns import qn
            ln = sh.line._get_or_add_ln()
            etree.SubElement(ln, qn("a:prstDash")).set("val", "dash")
        if self.label:
            s.text(self.x + 0.15, self.y + 0.07, self.w - 0.3, 0.4, P(self.label, size=self.ls, bold=True,
                                                                      color=self.lc))


class Arrow(El):
    """A straight arrow from (x1, y1) to (x2, y2); hl steps turn it blue and thick."""

    def __init__(self, x1, y1, x2, y2, dashed=False, color=MUTED, head=True, width=1.5, **kw):
        pad = 0.12
        super().__init__(min(x1, x2) - pad, min(y1, y2) - pad, abs(x2 - x1) + 2 * pad, abs(y2 - y1) + 2 * pad, **kw)
        self.p = (x1, y1, x2, y2)
        self.dashed, self.color, self.head, self.width = dashed, color, head, width

    def html(self):
        x1, y1, x2, y2 = self.p
        ox, oy = self.x, self.y
        a = [(x1 - ox) * PX, (y1 - oy) * PX, (x2 - ox) * PX, (y2 - oy) * PX]
        import math
        L = math.hypot(a[2] - a[0], a[3] - a[1]) or 1
        ux, uy = (a[2] - a[0]) / L, (a[3] - a[1]) / L
        hl_ = 18 if self.head else 0
        ex, ey = a[2] - ux * hl_, a[3] - uy * hl_
        tri = ""
        if self.head:
            px_, py_ = -uy, ux
            pts = [(a[2], a[3]), (ex + px_ * 9, ey + py_ * 9), (ex - px_ * 9, ey - py_ * 9)]
            tri = '<polygon points="' + " ".join(f"{u:.1f},{v:.1f}" for u, v in pts) + '"/>'
        dash = ' stroke-dasharray="10 8"' if self.dashed else ""
        svg = (f'<svg class="ar" width="{self.w * PX:.0f}" height="{self.h * PX:.0f}" style="--c:#{self.color};'
               f'--sw:{self.width * 2:.1f}px"><line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{ex:.1f}" y2="{ey:.1f}"{dash} '
               f'pathLength="1"/>{tri}</svg>')
        return self.wrap(svg)

    def pptx(self, s, k):
        x1, y1, x2, y2 = self.p
        lit = self.lit(k)
        s.line(x1, y1, x2, y2, color=BLUE if lit else self.color, width=2.5 if lit else self.width,
               arrow=self.head, dash=self.dashed)


class Stat(El):
    """A big number and a label. HTML counts up from zero when the slide opens."""

    def __init__(self, x, y, w, h, value, label, dec=0, suffix="", big=48, label_size=16, color=BLUE, **kw):
        super().__init__(x, y, w, h, **kw)
        self.value, self.label, self.dec, self.suffix, self.big, self.ls, self.color = (value, label, dec, suffix, big,
                                                                                         label_size, color)

    def text(self):
        return f"{self.value:,.{self.dec}f}{self.suffix}"

    def html(self):
        return self.wrap(f'<div class="stat"><div class="sn" style="font-size:{self.big * 2}px;color:#{self.color}" '
                         f'data-count="{self.value}" data-dec="{self.dec}" data-suffix="{escape(self.suffix)}">'
                         f'{self.text()}</div><div class="sl" style="font-size:{self.ls * 2}px">{md(self.label)}</div>'
                         f'</div>')

    def pptx(self, s, k):
        s.stat(self.x, self.y, self.w, self.text(), self.label, big_size=self.big, label_size=self.ls,
               color=self.color, h=self.h)


class Link(El):
    def __init__(self, x, y, w, h, url, text=None, size=14, align="l", **kw):
        super().__init__(x, y, w, h, **kw)
        self.url, self.label, self.size, self.align = url, text, size, align

    def html(self):
        u = self.url if self.url.startswith("http") else "https://" + self.url
        return self.wrap(f'<a class="lk" href="{escape(u)}" target="_blank" rel="noopener" style="font-size:'
                         f'{self.size * 2}px;text-align:{ {"l": "left", "c": "center", "r": "right"}[self.align]}">'
                         f'{escape(self.label or self.url)}</a>')

    def pptx(self, s, k):
        s.link(self.x, self.y, self.w, self.h, self.url, text=self.label, size=self.size, align=self.align)


class Raw(El):
    """Custom HTML (an animation), with an optional function that draws its PowerPoint version."""

    def __init__(self, x, y, w, h, inner, draw=None, **kw):
        super().__init__(x, y, w, h, **kw)
        self.inner, self.draw = inner, draw

    def html(self):
        return self.wrap(self.inner)

    def pptx(self, s, k):
        if self.draw:
            self.draw(s, k)


class Slide:
    def __init__(self, title, els=(), steps=0, cls="", notes="", kind="content", builds=False, optional=False,
                 pptx_title=None):
        self.title, self.els, self.steps, self.cls, self.notes = title, list(els), steps, cls, notes.strip()
        self.kind, self.builds, self.optional, self.pptx_title = kind, builds, optional, pptx_title
