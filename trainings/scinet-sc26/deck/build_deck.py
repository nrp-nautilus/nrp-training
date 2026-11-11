"""Build the PowerPoint fallback of the SCinet deck on the SDSC template.

    python3 deck/snapshot.py      # optional: refresh the numbers from the cluster (read-only; needs kubectl)
    python3 deck/make_map.py      # the map images
    python3 deck/build_deck.py    # -> slides/scinet-nrp.pptx (no notes), deck/presenter/scinet-nrp.pptx (notes)

The slides come from slides.py, the same definitions build_html.py animates. Here each slide shows
its final state; slides marked builds=True become one copy per step instead (a fake animation, paged
through in the PDF), all with the same slide number. After you edit the .pptx in PowerPoint, treat
it as the source: rerunning this overwrites it.
"""
from pathlib import Path

from pptx.util import Inches, Pt

import slides as SL
from deckkit import GOLD, SANS_BLACK, WHITE, Deck, P, fill_tf

HERE = Path(__file__).resolve().parent
TRAINING = HERE.parent
import os
_alt = os.environ.get("DECK_OUT")          # DECK_OUT=<dir>: test builds go there, not to slides/ and presenter/
OUT = Path(_alt) / "scinet-nrp.pptx" if _alt else TRAINING / "slides" / "scinet-nrp.pptx"
FOOT = "NRP"

deck = Deck(HERE / "assets" / "sdsc_template.pptx")


def title_slide(sd):
    s = deck.slide(layout="1_Title Slide", section=None)
    t = s.s.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.67), Inches(1.0), Inches(12.0), Inches(2.4)
    tf = t.text_frame
    tf.text = ""
    for i, line in enumerate(SL.TITLE):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 0.8
        r = p.add_run(); r.text = line; r.font.size = Pt(48); r.font.italic = False
    sub = [ph for ph in s.s.placeholders if ph.placeholder_format.idx == 1][0]
    sub.left, sub.top, sub.width, sub.height = Inches(0.67), Inches(3.75), Inches(10.5), Inches(2.5)
    fill_tf(sub.text_frame, [P(SL.TAGLINE, size=28, font=SANS_BLACK, color=GOLD, after=14),
                             P(SL.SPEAKER, size=21, color=WHITE, after=6),
                             P(SL.EVENT, size=17, color="E7E6E6")])
    return s


def section_slide(sd):
    s = deck.slide(layout="Section Header - Reverse", section=FOOT)
    for ph in list(s.s.placeholders):
        if ph.placeholder_format.idx != 0:
            ph._element.getparent().remove(ph._element)
    tf = s.s.shapes.title.text_frame
    tf.text = ""
    tf.paragraphs[0].add_run().text = sd.title
    return s


def content_slide(sd, k, cont):
    layout = "Title Only - Reverse" if sd.kind == "reverse" else "Title Only"
    s = deck.slide(title=sd.title, layout=layout, section=FOOT, cont=cont)
    for e in sd.els:
        if e.in_pptx and e.visible(k):
            e.pptx(s, k)
    return s


for sd in SL.SLIDES:
    if sd.kind == "title":
        made = [title_slide(sd)]
        deck.n = 0                      # the title isn't numbered, as in the HTML
    elif sd.kind == "section":
        made = [section_slide(sd)]
    elif sd.builds:
        made = [content_slide(sd, k, k > 0) for k in range(sd.steps + 1)]
    else:
        made = [content_slide(sd, sd.steps, False)]
    for s in made:
        if sd.notes:
            s.notes(sd.notes)

PRESENTER = Path(_alt) / "presenter" if _alt else HERE / "presenter"   # with speaker notes; not committed
PRESENTER.mkdir(exist_ok=True)
deck.save(PRESENTER / OUT.name)
for sl in deck.p.slides:                        # the published copy has no speaker notes
    if sl.has_notes_slide:
        sl.notes_slide.notes_text_frame.text = ""
OUT.parent.mkdir(exist_ok=True)
deck.save(OUT)
from deckkit import CODE_WARNINGS  # noqa: E402

print(f"{OUT}  ({len(deck.p.slides)} slides, {deck.n} numbered)")
for w in CODE_WARNINGS:
    print("  WARNING", w)
