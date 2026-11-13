"""Build the animated HTML deck: one self-contained file on a fixed 1920 x 1080 stage.

    python3 deck/build_html.py      # -> slides/nairr-classroom.html, and deck/presenter/nairr-classroom.html with notes

The slides come from slides.py, the same definitions build_deck.py turns into the PowerPoint.
Present from a browser (or the training site):

    → ↓ Space PgDn   next step, then next slide      ← ↑ PgUp   back      (mouse clicks don't move the
    slides, so you can point at and select things; on a touch screen, swipe)
    F   full screen      N   speaker notes (presenter copy only)      Home / End   first / last slide
    #12 in the URL jumps to slide 12, #12.3 to its third step; ?print shows every slide in its final state.

Fonts come from Google Fonts (Teko, Source Sans 3, Source Code Pro); offline, the browser falls back
to system fonts. Images are embedded, so the file works on its own.
"""
from html import escape
from pathlib import Path

from elements import PX, md, uri
from make_map import LABEL_PX
import slides as SL

HERE = Path(__file__).resolve().parent
TRAINING = HERE.parent
TPL = HERE / "assets" / "template"
import os
# DECK_OUT=<dir> writes both copies there instead (for test builds that shouldn't touch the real files)
_alt = os.environ.get("DECK_OUT")
OUT = Path(_alt) / "nairr-classroom.html" if _alt else TRAINING / "slides" / "nairr-classroom.html"
PRESENTER_OUT = Path(_alt) / "nairr-classroom-notes.html" if _alt else HERE / "presenter" / "nairr-classroom.html"

CSS = """
:root { --navy:#182B49; --blue:#00629B; --gold:#FFCD00; --orange:#EB6834; --card:#EEF3F8; --card2:#DDE8F2; --body:#2B3648;
  --muted:#5C6778; --light:#C9D4E3; --bar:#747678; --dim:#F3F4F6; --dimt:#A3ABB6; --red:#B3261E; --green:#1B7F55;
  --f-title:'Teko','Arial Narrow',sans-serif; --f-body:'Source Sans 3','Source Sans Pro','Helvetica Neue',Arial,sans-serif;
  --f-mono:'Source Code Pro',Menlo,Consolas,monospace; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; height: 100%; background: #0b0f17; overflow: hidden; font-family: var(--f-body); color: var(--body); }
#deckStage { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }
.slide { position: absolute; inset: 0; background: #fff; opacity: 0; visibility: hidden; transition: opacity .35s; overflow: hidden; }
.slide.active { opacity: 1; visibility: visible; }
.slide .ttl { position: absolute; left: 72px; top: 30px; width: 1776px; font: 600 80px/1.15 var(--f-title); color: var(--blue); letter-spacing: .01em; }
.bar { position: absolute; left: 0; right: 0; bottom: 0; height: 79px; background: var(--bar); }
.bar img { position: absolute; left: 26px; top: 16px; height: 46px; }
.bar .num { position: absolute; right: 300px; top: 24px; color: #fff; font: 600 22px var(--f-body); }
.a, .sb { position: absolute; }
.a p { line-height: 1.25; }
.notes { display: none; }
b { font-weight: 700; color: inherit; }
code { font-family: var(--f-mono); font-size: .9em; }
.acc { color: var(--blue); }
/* bullets */
ul.bl { list-style: none; }
ul.bl li { position: relative; line-height: 1.22; }
ul.bl li.l0 { padding-left: 1.05em; margin-top: var(--gap, .55em); }
ul.bl li.l0:first-child { margin-top: 0; }
ul.bl li.l0::before { content: "•"; position: absolute; left: .15em; color: var(--navy); }
ul.bl li.l1 { padding-left: 2.1em; font-size: .85em; margin-top: .2em; }
ul.bl li.l1::before { content: "•"; position: absolute; left: 1.2em; color: var(--navy); }
/* text bits */
.dh { font: 700 34px/1.2 var(--f-body); color: var(--navy); text-align: center; }
.dh.l { text-align: left; }
.cap { font-size: 26px; color: var(--muted); }
.cap.c { text-align: center; }
.lk { display: block; color: var(--blue); text-decoration: underline; font-style: italic; }
/* boxes, frames, arrows */
.bx { width: 100%; height: 100%; border-radius: 14px; background: var(--card); border: 2px solid #C9D4E3; display: flex;
  flex-direction: column; justify-content: center; padding: 6px 14px; transition: background .45s, border-color .45s; }
.bx .bh { font-weight: 700; color: var(--navy); line-height: 1.08; transition: color .45s; }
.bx .bs { color: var(--body); line-height: 1.15; margin-top: 3px; transition: color .45s; }
.bx .bs.mono { font-family: var(--f-mono); }
.bx.white { background: #fff; border-color: #B9C7D8; }
.bx.dim { background: var(--dim); border-color: #E3E6EA; } .bx.dim .bh { color: var(--dimt); } .bx.dim .bs { color: #B9C0C9; }
.bx.orange { background: #FDEBE3; border: 4px solid var(--orange); }
.bx.gold { background: #FFF4CC; border-color: #E9B55C; }
.bx.red { background: #F6D6D3; border-color: #D98C85; }
.bx.green { background: #D3EEE1; border-color: #7CC4A2; }
.bx.active, .a.hl > .bx { background: var(--navy); border-color: var(--navy); }
.bx.active .bh, .a.hl > .bx .bh { color: #fff; } .bx.active .bs, .a.hl > .bx .bs { color: var(--light); }
.frame { width: 100%; height: 100%; position: relative; }
.frame .fl { position: absolute; left: 20px; top: 8px; font-weight: 700; }
.ar { display: block; overflow: visible; }
.ar line { stroke: var(--c); stroke-width: var(--sw); transition: stroke .4s, stroke-width .4s; }
.ar polygon { fill: var(--c); transition: fill .4s; }
.a.hl .ar line { stroke: var(--blue); stroke-width: 5px; } .a.hl .ar polygon { fill: var(--blue); }
/* images, code, tables, stats */
.im { display: block; max-width: 100%; max-height: 100%; width: auto; height: auto; }
.framed { border: 2px solid #DDE8F2; }
.code { width: 100%; height: 100%; background: var(--navy); border-radius: 8px; padding: 20px 24px; color: #fff; overflow: hidden; }
.code pre { font-family: var(--f-mono); line-height: 1.3; white-space: pre; }
.code .ln { display: block; transition: background .4s; border-radius: 3px; }
.code .ln.hl { background: rgba(255,205,0,.24); }
.code .cm { color: #9FB3CC; } .code .st { color: var(--gold); }
.code .ct { color: var(--gold); font: 600 .95em var(--f-body); margin-bottom: 8px; }
table.tb { width: 100%; border-collapse: collapse; }
table.tb th { background: var(--navy); color: #fff; text-align: left; padding: 6px 14px; font-weight: 700; height: var(--rh); }
table.tb td { padding: 4px 14px; vertical-align: middle; line-height: 1.15; height: var(--rh); }
table.tb td:first-child { font-weight: 700; } table.tb.nobold td:first-child { font-weight: 400; }
table.tb tbody tr:nth-child(odd) td { background: var(--card); }
table.tb td.mono { font-family: var(--f-mono); font-weight: 400; font-size: .92em; }
.stat .sn { font-family: var(--f-title); font-weight: 600; line-height: .8; }
.stat .sl { color: var(--body); margin-top: 6px; line-height: 1.15; }
/* section, title and reverse slides */
.slide.section { background: var(--navy); }
.slide.section .ttl { top: 400px; left: 131px; font-size: 150px; color: #fff; }
.slide.reverse { background: var(--navy); } .slide.reverse .ttl { color: #fff; }
.qrow { display: flex; gap: 40px; font-size: 34px; color: var(--light); line-height: 2.05; }
.qrow span { width: 446px; } .qrow a { color: var(--gold); font: 700 30px var(--f-mono); text-decoration: none; }
.slide.title { background: #0d1a2e center/cover no-repeat; }
.slide.title .shade { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(24,43,73,.93) 0%, rgba(24,43,73,.8) 55%, rgba(24,43,73,.35) 100%); }
.slide.title .tt { position: absolute; left: 96px; top: 150px; width: 1700px; color: #fff; font: 600 104px/0.92 var(--f-title); }
.slide.title .tg { position: absolute; left: 96px; top: 560px; width: 1500px; color: var(--gold); font: 900 56px/1.1 var(--f-body); }
.slide.title .tn { position: absolute; left: 96px; top: 700px; color: #fff; font-size: 42px; }
.slide.title .te { position: absolute; left: 96px; top: 765px; color: #E7E6E6; font-size: 34px; }
/* build steps: data-s shows from step k; data-only shows at listed steps */
[data-s], [data-only] { transition: opacity .5s ease, transform .5s ease; }
[data-s] { opacity: 0; transform: translateY(14px); }
[data-s].on { opacity: 1; transform: none; }
[data-only] { opacity: 0; pointer-events: none; }
[data-only].on { opacity: 1; pointer-events: auto; }
.slide [data-only]:not(.on), .slide [data-s]:not(.on) { opacity: 0 !important; }
/* blocks that ease in when a slide opens */
.stagger li, .stagger p, .stagger .qrow, .rows tbody tr, .pop, .rise { opacity: 0; transform: translateY(12px); transition: opacity .5s ease, transform .5s ease; }
.slide.active .stagger li, .slide.active .stagger p, .slide.active .stagger .qrow, .slide.active .rows tbody tr,
.slide.active .pop, .slide.active .rise { opacity: 1; transform: none; }
""" + "".join(f".slide.active .stagger li:nth-child({i}), .slide.active .stagger p:nth-child({i}), "
              f".slide.active .stagger .qrow:nth-child({i}), .slide.active .rows tbody tr:nth-child({i}) "
              f"{{ transition-delay: {0.1 + i * 0.1:.2f}s; }}\n" for i in range(1, 20)) + """
.slide.active .pop { transition-delay: .35s; }
/* maps: pins drop in */
.usmap { display: block; overflow: visible; }
.usmap .land { fill: #E6ECF3; stroke: #fff; stroke-width: 1.2; stroke-linejoin: round; }
.usmap .pin { opacity: 0; transform: translateY(-70px); transition: transform .55s cubic-bezier(.3,1.45,.55,1), opacity .2s; }
.usmap .pin use { stroke: #fff; stroke-width: 1.2; } .usmap .pin circle { fill: #fff; }
.usmap .k-other use { fill: var(--blue); } .usmap .k-ops use { fill: var(--navy); } .usmap .k-llm use { fill: var(--orange); }
.usmap .k-llm text { font: 700 17px var(--f-body); fill: var(--navy); }
.usmap .pl { font: 700 LABELpx var(--f-body); fill: var(--navy); paint-order: stroke; stroke: #fff; stroke-width: 7px; stroke-linejoin: round; opacity: 0; transition: opacity .4s; }
.slide.active .usmap .k-ops, .slide.active .usmap .pl, .whatnrp:not([data-cur="0"]) .usmap .k-other,
.slide.active .usmap.llm .pin { opacity: 1; transform: none; transition-delay: var(--d); }
/* numbers */
.numbers .frame { transition: none; }
/* bar charts */
.hbars { width: 100%; }
.hb { display: flex; align-items: center; height: 69px; font-size: 24px; }
.storage .hb { height: 63px; }
.hb .hn { text-align: right; padding-right: 16px; color: var(--body); white-space: nowrap; flex: none; }
.hb .ht { flex: 1; position: relative; display: flex; align-items: center; height: 100%; }
.hb .ht i { display: block; height: 34px; width: 0; border-radius: 5px; transition: width 1s cubic-bezier(.3,.7,.2,1); }
.hb .ht i.u { position: absolute; left: 0; top: 50%; margin-top: -17px; background: var(--blue); }
.slide.active .hb .ht i { width: calc(var(--w) * .78); }
.hb em { font-style: normal; color: var(--muted); font-size: 22px; margin-left: 12px; white-space: nowrap; }
/* GitOps: the drift is reverted */
.gitops .drift .bx { transition: opacity .6s, background .6s; }
.gitops[data-cur="3"] .drift .bx { opacity: .4; background: var(--dim); }
.gitops[data-cur="3"] .drift .bh { text-decoration: line-through; }
/* NetBox: LLDP frames travel the cable */
.netbox .lldp { position: absolute; left: 50%; width: 22px; height: 22px; margin-left: -11px; border-radius: 50%; background: var(--orange); border: 3px solid #fff; top: 0; }
.netbox[data-cur="1"] .lldp { animation: lldp 1.1s linear infinite; }
@keyframes lldp { 0% { top: 0; } 100% { top: 115px; } }
/* perfSONAR mesh */
.mesh { display: block; overflow: visible; }
.mesh .all { stroke: var(--blue); stroke-width: .35; fill: none; opacity: 0; transition: opacity 1.4s; }
.perfsonar[data-cur="2"] .mesh .all { opacity: .1; }
.mesh .spokes line { stroke: var(--orange); stroke-width: 1.6; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: .85; }
.perfsonar:not([data-cur="0"]) .mesh .spokes line { stroke-dashoffset: 0; transition: stroke-dashoffset .5s var(--d); }
.mesh .dots circle { fill: var(--navy); }
.mesh .labs text { font: 700 22px var(--f-body); fill: var(--navy); }
/* sharing GPUs: slots fill with opportunistic work, then the owner takes two back */
.fairshare .sb, .fairshare .a > .gs { position: static; }
.fairshare .a:has(.gs) { display: flex; gap: 12px; }
.gs { flex: 1; height: 346px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font: 700 25px var(--f-body); transition: background .5s, color .5s; }
.gs span { display: none; writing-mode: vertical-rl; transform: rotate(180deg); }
.gs.own { background: var(--navy); color: #fff; } .gs.own .o { display: block; }
.gs.idle { background: #DDE1E6; color: #6B7480; } .fairshare[data-cur="0"] .gs.idle .i { display: block; }
.fairshare:not([data-cur="0"]) .gs.idle { background: #F6D58C; color: var(--navy); }
.fairshare:not([data-cur="0"]) .gs.idle .p { display: block; }
.fairshare[data-cur="2"] .gs.g2, .fairshare[data-cur="2"] .gs.g3 { background: var(--navy); color: #fff; animation: preempt 1.2s ease; }
.fairshare[data-cur="2"] .gs.g2 .p, .fairshare[data-cur="2"] .gs.g3 .p { display: none; }
.fairshare[data-cur="2"] .gs.g2 .x, .fairshare[data-cur="2"] .gs.g3 .x { display: block; }
@keyframes preempt { 0%, 40% { background: var(--red); } 100% { background: var(--navy); } }
/* task models: the first choice is ejected */
.eject { width: 100%; height: 100%; border-radius: 12px; background: #B3261E; color: #fff; font: 700 26px var(--f-body); display: flex; align-items: center; justify-content: center; }
.scavenge .rep { transition: opacity .6s .9s; } .scavenge[data-cur="1"] .rep.r2 { opacity: .2; }
/* GPU job callouts */
.gpujob .co { transition: opacity .4s; }
.gpujob:not([data-cur="0"]) .co:not(.hl) { opacity: .35; }
/* code that types in when the slide opens */
.code.typed .ln { opacity: 0; }
.slide.active .code.typed .ln { animation: typein .01s forwards; animation-delay: calc(.4s + var(--i) * .16s); }
@keyframes typein { to { opacity: 1; } }
/* ways to run work (from the UCLA deck) */
.runways .lw { transition: opacity .5s, transform .5s; }
.runways[data-cur="1"] .b0, .runways[data-cur="2"] .b0, .runways[data-cur="2"] .b1, .runways[data-cur="3"] .lw { opacity: .4 !important; }
.code.one { padding: 12px 22px; display: flex; align-items: center; }
.gantt { position: absolute; inset: 0; font-family: var(--f-mono); }
.gantt .plab, .gantt .glab, .gantt .tlab { position: absolute; left: 0; font: 700 24px var(--f-body); color: var(--navy); line-height: 58px; }
.gantt .plab { top: 0; line-height: 46px; color: #C27C0E; }
.gantt .tlab { left: auto; right: 0; font: 400 22px var(--f-body); color: var(--muted); line-height: 30px; }
.gantt .pc { position: absolute; top: 0; width: 120px; height: 46px; line-height: 42px; text-align: center; font-size: 19px; color: var(--navy); background: #FFF4DE; border: 2px solid #E9B55C; border-radius: 10px; opacity: 0; }
.gantt .trk, .lc .trk { position: absolute; left: 115px; width: 775px; height: 58px; background: var(--dim); border-radius: 12px; }
.gantt .gb, .gantt .gl { position: absolute; height: 50px; border-radius: 10px; }
.gantt .gb { background: var(--blue); width: 0; }
.gantt .gl { width: 0; overflow: hidden; white-space: nowrap; line-height: 50px; text-align: left; padding-left: 16px; font-size: 20px; font-weight: 600; color: #fff; opacity: 0; }
.gantt .nowl { position: absolute; top: 62px; height: 284px; width: 3px; left: 115px; background: var(--gold); opacity: 0; }
.gantt .tax { position: absolute; left: 115px; width: 775px; height: 2px; background: var(--muted); }
.runways[data-cur="3"] .gantt .pc { animation: show .3s ease var(--a) forwards, leave .4s ease var(--b) forwards; }
.runways[data-cur="3"] .gantt .gb { animation: grow var(--du) linear var(--t0) both, done .4s ease var(--t1) forwards; }
.runways[data-cur="3"] .gantt .gl { animation: grow var(--du) linear var(--t0) both, show .25s linear calc(var(--t0) + .3s) forwards, darkt .4s ease var(--t1) forwards; }
.runways[data-cur="3"] .gantt .nowl { animation: sweepnow var(--du) linear var(--t0) forwards; }
@keyframes show { to { opacity: 1; } }
@keyframes hide { from { opacity: 1; } to { opacity: 0; } }
@keyframes leave { from { opacity: 1; } to { opacity: 0; transform: translateY(40px); } }
@keyframes grow { from { width: 0; } to { width: var(--w); } }
@keyframes done { to { background: #8FB0CF; } }
@keyframes darkt { to { color: var(--navy); } }
@keyframes sweepnow { 0% { left: 115px; opacity: 1; } 96% { opacity: 1; } 100% { left: 890px; opacity: 0; } }
.lc { position: absolute; inset: 0; }
.lc .lcl { position: absolute; left: 0; top: 40px; line-height: 58px; font: 700 24px var(--f-body); color: var(--navy); }
.lc .trk { top: 40px; }
.lc .sg { position: absolute; top: 44px; height: 50px; width: 0; border-radius: 10px; overflow: hidden; white-space: nowrap; line-height: 50px; text-indent: 16px; font: 600 22px var(--f-body); color: #fff; }
.lc .sg.run { background: var(--blue); }
.lc .sg.idle { background: repeating-linear-gradient(45deg, #F2C46D 0 10px, #F8DDA6 10px 20px); color: var(--navy); }
.lc .mk { position: absolute; top: 30px; width: 3px; height: 78px; opacity: 0; }
.lc .mt { position: absolute; font: 600 24px var(--f-body); line-height: 30px; white-space: nowrap; opacity: 0; }
.lc .mk.neutral { background: var(--muted); } .lc .mt.neutral { color: var(--body); }
.lc .mk.ok { background: #1B7F55; } .lc .mt.ok { color: #1B7F55; }
.lc .mk.bad { background: #B3261E; } .lc .mt.bad { color: #B3261E; }
""" + "".join(f'.runways[data-cur="{k}"] .lc{k} .sg {{ animation: grow var(--du) linear var(--t0) both; }}\n'
              f'.runways[data-cur="{k}"] .lc{k} .mk, .runways[data-cur="{k}"] .lc{k} .mt '
              f'{{ animation: show .3s ease var(--t) forwards; }}\n' for k in range(3)) + """
.kterm { padding: 18px 24px; } .kterm .ln { color: #C9D4E3; } .kterm .ln.cmd { color: #fff; }
.podterm .ln { opacity: 0; }
.runways[data-cur="1"] .podterm .ln { animation: show .01s linear calc(.3s + var(--i) * .4s) forwards; }
.depbox { width: 100%; height: 100%; border: 3px dashed #B9C7D8; border-radius: 14px; padding: 22px 26px; }
.dpods { display: flex; gap: 20px; margin-top: 22px; }
.dpod { flex: 1; height: 110px; border-radius: 12px; background: var(--card); border: 2px solid #C9D4E3; display: flex; flex-direction: column; justify-content: center; padding: 0 18px; position: relative; }
.dpod code { font-size: 21px; color: var(--navy); } .dpod b { font-size: 24px; color: #1B7F55; margin-top: 6px; }
.dpod.swapper span { position: absolute; left: 18px; right: 18px; top: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; }
.dpod .p2, .dpod .p3 { opacity: 0; } .dpod .p2 b { color: #B3261E; }
.runways[data-cur="2"] .dpod .p1 { animation: hide .2s linear 1.95s forwards; }
.runways[data-cur="2"] .dpod .p2 { animation: show .2s linear 1.95s forwards, hide .3s linear 2.6s forwards; }
.runways[data-cur="2"] .dpod .p3 { animation: show .4s ease 2.6s forwards; }
.runways[data-cur="2"] .dpod.swapper { animation: crashbg .9s ease 1.95s; }
@keyframes crashbg { 0%, 100% { background: var(--card); } 25%, 75% { background: #F6D6D3; border-color: #B3261E; } }
/* notes overlay and pager */
#notes { position: fixed; left: 0; right: 0; bottom: 0; max-height: 40%; overflow: auto; background: rgba(10,15,25,.94); color: #f2f2f2; font: 18px/1.5 var(--f-body); padding: 18px 28px; display: none; white-space: pre-wrap; z-index: 10; }
body.show-notes #notes { display: block; }
#help { position: fixed; right: 12px; bottom: 10px; color: rgba(255,255,255,.75); background: rgba(0,0,0,.45); padding: 4px 8px; border-radius: 4px; font: 13px var(--f-body); z-index: 5; animation: helpfade 1s 6s forwards; }
@keyframes helpfade { to { opacity: 0; } }
/* print: every slide on its own page, in its final state */
body.print { overflow: visible; background: #fff; }
body.print #deckStage { position: static; transform: none !important; width: auto; height: auto; }
body.print .slide { position: relative; opacity: 1; visibility: visible; width: 1920px; height: 1080px; page-break-after: always; }
body.print [data-s], body.print .stagger li, body.print .stagger p, body.print .pop, body.print .rise, body.print .rows tbody tr { opacity: 1 !important; transform: none !important; }
body.print #help, body.print .lldp { display: none; }
body.print .gantt * { animation: none !important; } body.print .gantt .gb { width: var(--w) !important; background: #8FB0CF; }
body.print .gantt .gl { opacity: 1; color: var(--navy); width: var(--w); } body.print .usmap .pin, body.print .usmap .pl { opacity: 1; transform: none; }
body.print .runways .lw { opacity: 1 !important; } body.print .gantt .pc, body.print .gantt .nowl { display: none; }
body.print .mesh .spokes line { stroke-dashoffset: 0; } body.print .code.typed .ln { opacity: 1; }
@page { size: 1920px 1080px; margin: 0; }
"""
CSS = CSS.replace("LABELpx", f"{LABEL_PX}px")

JS = r"""
(function () {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const stage = document.getElementById('deckStage');
  const notes = document.getElementById('notes');
  const print = new URLSearchParams(location.search).has('print');
  let cur = 0, step = 0;
  function fit() {
    if (print) return;
    const f = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(${(innerWidth - 1920 * f) / 2}px, ${(innerHeight - 1080 * f) / 2}px) scale(${f})`;
  }
  function has(list, k) { return list.split(' ').includes(String(k)); }
  function apply(s, k) {
    s.dataset.cur = k;
    s.querySelectorAll('[data-s]').forEach(e => e.classList.toggle('on', +e.dataset.s <= k));
    s.querySelectorAll('[data-only]').forEach(e => e.classList.toggle('on', has(e.dataset.only, k)));
    s.querySelectorAll('[data-hl]').forEach(e => e.classList.toggle('hl', has(e.dataset.hl, k)));
  }
  function fmt(v, dec, suf) { return v.toLocaleString('en-US', {minimumFractionDigits: dec, maximumFractionDigits: dec}) + suf; }
  function countUp(s) {
    s.querySelectorAll('[data-count]').forEach(e => {
      const to = +e.dataset.count, dec = +e.dataset.dec || 0, suf = e.dataset.suffix || '';
      let n = 0; const N = 45;               // timers, not animation frames: they also run in headless captures
      const id = setInterval(() => { n++; const p = n / N; e.textContent = fmt(to * (1 - Math.pow(1 - p, 3)), dec, suf);
        if (n >= N) clearInterval(id); }, 33);
    });
  }
  function show(i, atEnd) {
    const prev = cur;
    cur = Math.max(0, Math.min(i, slides.length - 1));
    const s = slides[cur];
    step = atEnd ? +s.dataset.steps : 0;
    slides.forEach((x, k) => x.classList.toggle('active', k === cur));
    apply(s, step);
    if (prev !== cur || !s.dataset.counted) { countUp(s); s.dataset.counted = 1; }
    notes.textContent = (s.querySelector('.notes') || {}).textContent || '';
    history.replaceState(null, '', '#' + (cur + 1));
  }
  function next() { const s = slides[cur]; if (step < +s.dataset.steps) { step++; apply(s, step); } else if (cur < slides.length - 1) show(cur + 1); }
  function prev() { const s = slides[cur]; if (step > 0) { step--; apply(s, step); } else if (cur > 0) show(cur - 1, true); }
  if (print) {
    document.body.classList.add('print');
    slides.forEach(s => { s.classList.add('active'); apply(s, +s.dataset.steps); });
    return;
  }
  document.addEventListener('keydown', e => {
    if (['ArrowRight', 'ArrowDown', ' ', 'PageDown'].includes(e.key)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); prev(); }
    else if (e.key === 'Home') show(0); else if (e.key === 'End') show(slides.length - 1);
    else if (e.key === 'n' || e.key === 'N') NOTES_TOGGLE;
    else if (e.key === 'f' || e.key === 'F') { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => {}); }
  });
  let x0 = null;
  document.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  document.addEventListener('touchend', e => { if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 50) (dx < 0 ? next : prev)(); x0 = null; });
  window.addEventListener('resize', fit); fit();
  function fromHash() {                       // #12 is slide 12; #12.3 is slide 12 at step 3
    const m = (location.hash || '').match(/^#(\d+)(?:\.(\d+))?/);
    if (!m) return show(0);
    if (+m[1] - 1 !== cur || !m[2] || !slides[cur].classList.contains('active')) show(+m[1] - 1);
    if (m[2]) { step = Math.min(+m[2], +slides[cur].dataset.steps); apply(slides[cur], step); }
  }
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
"""

WORDMARK = uri(TPL / "wordmark.png")
TITLE_BG = uri(TPL / "title.jpg")


def number_slides():
    n, out = 0, []
    for sd in SL.SLIDES:
        n += sd.kind != "title"
        out.append(n)
    return out


def render(sd, n, with_notes):
    notes = f'<div class="notes">{escape(sd.notes)}</div>' if with_notes else ""
    if sd.kind == "title":
        return (f'<section class="slide title" data-steps="0" style="background-image:url({TITLE_BG})">'
                f'<div class="shade"></div><div class="tt">{"<br>".join(map(escape, SL.TITLE))}</div>'
                f'<div class="tg">{escape(SL.TAGLINE)}</div><div class="tn">{md(SL.SPEAKER)}</div>'
                f'<div class="te">{escape(SL.EVENT)}</div>{notes}</section>')
    bar = (f'<footer class="bar"><img src="{WORDMARK}" alt="San Diego Supercomputer Center">'
           f'<span class="num">{n}</span></footer>')
    cls = {"section": "section", "reverse": "reverse"}.get(sd.kind, "")
    body = "".join(e.html() for e in sd.els)
    return (f'<section class="slide {cls} {sd.cls}" data-steps="{sd.steps}"><h1 class="ttl">{escape(sd.title)}</h1>'
            f'{body}{bar}{notes}</section>')


def page(with_notes):
    nums = number_slides()
    help_ = "→ next · ← back · N notes · F full screen" if with_notes else "→ next · ← back · F full screen"
    js = JS.replace("NOTES_TOGGLE", "document.body.classList.toggle('show-notes')" if with_notes else "0")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(SL.DECK_TITLE)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Teko:wght@500;600&family=Source+Sans+3:wght@400;600;700;900&family=Source+Code+Pro:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body><div id="deckStage">{"".join(render(s, n, with_notes) for s, n in zip(SL.SLIDES, nums))}</div>
<div id="notes"></div><div id="help">{help_}</div>
<script>{js}</script></body></html>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    PRESENTER_OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page(False))              # the published deck: no speaker notes
    PRESENTER_OUT.write_text(page(True))     # for presenting: N shows the notes; not committed
    print(f"{OUT}  ({len(SL.SLIDES)} slides, {OUT.stat().st_size / 1e6:.1f} MB), notes copy: {PRESENTER_OUT}")
    opt = [s.title for s in SL.SLIDES if s.optional]
    print(f"  optional ({len(opt)}): {', '.join(opt)}")
