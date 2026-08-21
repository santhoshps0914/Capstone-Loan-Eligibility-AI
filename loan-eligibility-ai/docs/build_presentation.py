"""Build the Loan Eligibility AI capstone presentation.

    python docs/build_presentation.py

Reads the screenshots in docs/screenshots/ and writes
Loan_Eligibility_AI_Presentation.pptx (16:9) in the project root.

Every factual figure in the deck comes from this repository: thresholds from
agents/eligibility_agent.py, endpoints from service/coordinator_service.py,
latency and test counts measured locally (see the METRICS block below).
"""

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "screenshots"
DERIVED = SHOTS / "derived"
DERIVED.mkdir(exist_ok=True)
OUTFILE = ROOT / "Loan_Eligibility_AI_Presentation.pptx"

TEAM = ["Ankita Vyas", "Santhoshkumar PS", "Vandana H K", "Shubham Kumar"]
DECK_DATE = "August 2026"
FOOTER = "Loan Eligibility AI  ·  Capstone Demonstration"

# Measured on the development machine, single Uvicorn worker, 60 sequential
# requests. Reproduce with docs/capture_screenshots.py + pytest -q.
METRICS = {
    "tests": "43",
    "p50": "4 ms",
    "p95": "5 ms",
    "chat_p50": "5 ms",
    "modules": "13",
}

# ---------------------------------------------------------------- design system

SLIDE_W, SLIDE_H = 13.333, 7.5
M = 0.62                      # page margin
CW = SLIDE_W - 2 * M          # content width

INK = "0E1A33"
INK_SOFT = "1B2C52"
INDIGO = "4F46E5"
VIOLET = "7C3AED"
CYAN = "06B6D4"
GREEN = "15A34A"
AMBER = "D97706"
RED = "DC2626"
TEXT = "1F2937"
MUTED = "6B7280"
FAINT = "9AA3B2"
LINE = "E3E8F0"
SURF = "F6F8FC"
WHITE = "FFFFFF"

FONT = "Calibri"

ACCENTS = [INDIGO, VIOLET, CYAN, GREEN, AMBER, RED]


def rgb(value):
    return RGBColor.from_string(value)


def shape(slide, kind, x, y, w, h, fill=None, line=None, line_w=1.0, radius=None):
    shp = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(fill)
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = rgb(line)
        shp.line.width = Pt(line_w)
    if radius is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = radius
    shp.text_frame.word_wrap = True
    return shp


def rect(slide, x, y, w, h, **kw):
    return shape(slide, MSO_SHAPE.RECTANGLE, x, y, w, h, **kw)


def card(slide, x, y, w, h, fill=WHITE, line=LINE, radius=0.055):
    return shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h,
                 fill=fill, line=line, radius=radius)


def gradient_band(slide, x, y, w, h, c1=INDIGO, c2=VIOLET, angle=0):
    shp = rect(slide, x, y, w, h)
    shp.fill.gradient()
    shp.fill.gradient_angle = angle
    stops = shp.fill.gradient_stops
    stops[0].color.rgb = rgb(c1)
    stops[0].position = 0.0
    stops[1].color.rgb = rgb(c2)
    stops[1].position = 1.0
    return shp


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    return tf


def para(tf, text, size=14, bold=False, color=TEXT, space_before=0, space_after=4,
         align=PP_ALIGN.LEFT, first=False, line_spacing=1.06, italic=False,
         font=FONT, bullet=None, bullet_color=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    p.line_spacing = line_spacing
    if bullet:
        r = p.add_run()
        r.text = bullet + "  "
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.name = font
        r.font.color.rgb = rgb(bullet_color or INDIGO)
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    r.font.color.rgb = rgb(color)
    return p


def rich(tf, segments, size=13, space_after=5, first=False, align=PP_ALIGN.LEFT,
         line_spacing=1.08):
    """One paragraph from (text, bold, colour) segments."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after)
    p.line_spacing = line_spacing
    for seg in segments:
        text, bold, color = (seg + (None,) * (3 - len(seg)))[:3]
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bool(bold)
        r.font.name = FONT
        r.font.color.rgb = rgb(color or TEXT)
    return p


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ------------------------------------------------------------------ slide kinds

class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_W)
        self.prs.slide_height = Inches(SLIDE_H)
        self.blank = self.prs.slide_layouts[6]
        self.n = 0

    def _new(self):
        return self.prs.slides.add_slide(self.blank)

    def dark(self):
        slide = self._new()
        rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=INK)
        return slide

    def light(self):
        slide = self._new()
        rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)
        return slide

    def footer(self, slide, dark=False):
        self.n += 1
        col = FAINT if dark else MUTED
        tf = textbox(slide, M, SLIDE_H - 0.52, CW * 0.7, 0.3)
        para(tf, FOOTER, size=9, color=col, first=True, space_after=0)
        tf = textbox(slide, SLIDE_W - M - 1.2, SLIDE_H - 0.52, 1.2, 0.3)
        para(tf, f"{self.n:02d}", size=9, color=col, first=True, space_after=0,
             align=PP_ALIGN.RIGHT)

    def content(self, kicker, title, subtitle=None):
        """Standard content slide; returns (slide, y) where y is content top."""
        slide = self.light()
        gradient_band(slide, 0, 0, SLIDE_W, 0.085, INDIGO, VIOLET)
        tf = textbox(slide, M, 0.42, CW, 0.26)
        para(tf, kicker.upper(), size=9.5, bold=True, color=INDIGO, first=True,
             space_after=0)
        tf = textbox(slide, M, 0.72, CW, 0.55)
        para(tf, title, size=27, bold=True, color=INK, first=True, space_after=0)
        y = 1.44
        if subtitle:
            tf = textbox(slide, M, 1.34, CW * 0.86, 0.4)
            para(tf, subtitle, size=12.5, color=MUTED, first=True, space_after=0)
            y = 1.86
        self.footer(slide)
        return slide, y

    def section(self, number, title, blurb, presenter=None):
        slide = self.dark()
        gradient_band(slide, 0, 0, 0.22, SLIDE_H, INDIGO, VIOLET, angle=90)
        tf = textbox(slide, 1.5, 2.35, 3.0, 1.6)
        para(tf, number, size=96, bold=True, color=INDIGO, first=True, space_after=0)
        tf = textbox(slide, 3.4, 2.55, 8.4, 1.0)
        para(tf, title, size=36, bold=True, color=WHITE, first=True, space_after=6)
        para(tf, blurb, size=14, color="B9C2D6", space_after=0)
        if presenter:
            tf = textbox(slide, 3.4, 4.15, 8.4, 0.4)
            para(tf, presenter, size=11.5, bold=True, color=CYAN, first=True,
                 space_after=0)
        self.footer(slide, dark=True)
        return slide


# --------------------------------------------------------------- image helpers

def _load(name):
    return Image.open(SHOTS / name)


def _gap_near(img, ideal, window=0.14):
    """Nearest row to `ideal` that is empty background, so a multi-column
    re-flow never cuts a chat bubble in half."""
    px = img.convert("RGB")
    bg = px.getpixel((4, 4))
    span = int(img.height * window)
    for delta in range(0, span):
        for row in {ideal - delta, ideal + delta}:
            if not 1 <= row < img.height:
                continue
            line = px.crop((0, row, px.width, row + 1)).getcolors(maxcolors=px.width * 2)
            if line and len(line) == 1 and line[0][1] == bg:
                return row
    return ideal


def prepare(name, crop=None, columns=1, gap=26, bg=(241, 243, 247), out=None):
    """Crop / re-flow a screenshot and return the derived file path.

    crop     — (l, t, r, b) as fractions of the source size.
    columns  — slice a tall image into N vertical strips laid side by side.
    """
    img = _load(name)
    if crop:
        l, t, r, b = crop
        img = img.crop((int(l * img.width), int(t * img.height),
                        int(r * img.width), int(b * img.height)))
    if columns > 1:
        cuts = [_gap_near(img, round(img.height * i / columns))
                for i in range(1, columns)]
        bounds = [0] + cuts + [img.height]
        parts = [img.crop((0, bounds[i], img.width, bounds[i + 1]))
                 for i in range(columns)]
        tallest = max(p.height for p in parts)
        total_w = sum(p.width for p in parts) + gap * (columns - 1)
        canvas = Image.new("RGB", (total_w, tallest), bg)
        x = 0
        for p in parts:
            canvas.paste(p.convert("RGB"), (x, 0))
            x += p.width + gap
        img = canvas
    path = DERIVED / (out or f"{Path(name).stem}_d.png")
    img.convert("RGB").save(path)
    return path


def place_image(slide, path, x, y, w, h, border=LINE, shadow_pad=True):
    """Fit an image inside a box, centred, with a hairline frame."""
    img = Image.open(path)
    scale = min(w / img.width, h / img.height)
    iw, ih = img.width * scale, img.height * scale
    ix, iy = x + (w - iw) / 2, y + (h - ih) / 2
    if shadow_pad:
        card(slide, ix - 0.07, iy - 0.07, iw + 0.14, ih + 0.14,
             fill=SURF, line=LINE, radius=0.03)
    pic = slide.shapes.add_picture(str(path), Inches(ix), Inches(iy),
                                   Inches(iw), Inches(ih))
    if border:
        pic.line.color.rgb = rgb(border)
        pic.line.width = Pt(0.75)
    return pic


def callouts(slide, x, y, w, items, title=None, accent=INDIGO):
    """Numbered explanation column beside a screenshot."""
    if title:
        tf = textbox(slide, x, y, w, 0.3)
        para(tf, title.upper(), size=9.5, bold=True, color=accent, first=True,
             space_after=0)
        y += 0.38
    for i, (head, body) in enumerate(items, 1):
        badge = shape(slide, MSO_SHAPE.OVAL, x, y + 0.04, 0.26, 0.26,
                      fill=ACCENTS[(i - 1) % len(ACCENTS)])
        tf = badge.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para(tf, str(i), size=10.5, bold=True, color=WHITE, first=True,
             space_after=0, align=PP_ALIGN.CENTER)
        tf = textbox(slide, x + 0.4, y, w - 0.4, 0.4)
        para(tf, head, size=12.5, bold=True, color=INK, first=True, space_after=2)
        para(tf, body, size=11, color=MUTED, space_after=0, line_spacing=1.1)
        y += 0.42 + 0.185 * max(1, (len(body) // 46) + 1)
    return y


def chip(slide, x, y, w, h, label, value, accent=INDIGO):
    c = card(slide, x, y, w, h, fill=SURF, line=LINE)
    rect(slide, x, y, 0.055, h, fill=accent)
    tf = c.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.22)
    tf.margin_right = Inches(0.14)
    para(tf, value, size=19, bold=True, color=INK, first=True, space_after=1)
    para(tf, label, size=10.5, color=MUTED, space_after=0)
    return c


def feature_tile(slide, x, y, w, h, title, body, accent=INDIGO):
    c = card(slide, x, y, w, h)
    rect(slide, x + 0.001, y, 0.05, h, fill=accent)
    tf = c.text_frame
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.16)
    tf.margin_top = Inches(0.14)
    para(tf, title, size=12.5, bold=True, color=INK, first=True, space_after=3)
    para(tf, body, size=10.5, color=MUTED, space_after=0, line_spacing=1.1)
    return c


def flow_node(slide, x, y, w, h, title, lines, fill=WHITE, accent=INDIGO,
              title_color=None):
    c = card(slide, x, y, w, h, fill=fill, line=LINE)
    rect(slide, x + 0.001, y, 0.05, h, fill=accent)
    tf = c.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.12)
    para(tf, title, size=12, bold=True, color=title_color or INK, first=True,
         space_after=2)
    for ln in lines:
        para(tf, ln, size=9.8, color=MUTED, space_after=1, line_spacing=1.05)
    return c


def arrow(slide, x, y, w, h=0.16, color=FAINT, down=False):
    kind = MSO_SHAPE.DOWN_ARROW if down else MSO_SHAPE.RIGHT_ARROW
    return shape(slide, kind, x, y, w, h, fill=color)


# ------------------------------------------------------------------ slide build

def slide_title(d):
    slide = d.dark()
    gradient_band(slide, 0, 0, SLIDE_W, SLIDE_H * 0.055, INDIGO, VIOLET)
    # decorative corner block
    gradient_band(slide, SLIDE_W - 3.9, 0.9, 3.3, 5.6, "17224A", "0E1A33", angle=45)
    rect(slide, SLIDE_W - 3.9, 0.9, 0.06, 5.6, fill=VIOLET)

    tf = textbox(slide, M + 0.25, 1.55, 8.4, 0.4)
    para(tf, "CAPSTONE PROJECT  ·  AGENTIC AI", size=11, bold=True, color=CYAN,
         first=True, space_after=0)

    tf = textbox(slide, M + 0.25, 2.0, 8.7, 1.9)
    para(tf, "Loan Eligibility AI", size=54, bold=True, color=WHITE, first=True,
         space_after=6)
    para(tf, "A multi-agent decision engine with a customer-facing assistant",
         size=19, color="AEB9D2", space_after=0, line_spacing=1.14)

    rect(slide, M + 0.25, 4.22, 1.5, 0.045, fill=VIOLET)

    tf = textbox(slide, M + 0.25, 4.52, 9.0, 0.9)
    para(tf, "PRESENTED BY", size=9.5, bold=True, color=FAINT, first=True,
         space_after=6)
    rich(tf, [(TEAM[0] + "   ", True, WHITE), ("·   ", False, VIOLET),
              (TEAM[1] + "   ", True, WHITE), ("·   ", False, VIOLET),
              (TEAM[2] + "   ", True, WHITE), ("·   ", False, VIOLET),
              (TEAM[3], True, WHITE)], size=14, space_after=0)

    tf = textbox(slide, M + 0.25, 5.95, 9.0, 0.4)
    para(tf, f"Streamlit  ·  FastAPI  ·  Pydantic  ·  RAG retrieval  ·  Claude (optional)  |  {DECK_DATE}",
         size=11, color=FAINT, first=True, space_after=0)
    d.footer(slide, dark=True)
    notes(slide, (
        "Opening (30s). 'We built Loan Eligibility AI: a working full-stack system that turns a "
        "loan application into an explained decision in milliseconds, and then answers the "
        "customer's follow-up questions.' Name the four of us, then state the agenda. "
        "Everything shown in this deck is a screenshot of the running app on localhost — "
        "no mock-ups."))


def slide_agenda(d):
    slide, y = d.content("Agenda", "What we will cover in this session")
    items = [
        ("01", "Problem & solution", "Why manual eligibility review does not scale, and what we built instead.", INDIGO),
        ("02", "Architecture & design", "Multi-agent flow, the rule engine, the chatbot's two layers, repo map.", VIOLET),
        ("03", "Live walkthrough", "Every screen of the running app: form, three decisions, PDF, assistant, API.", CYAN),
        ("04", "Engineering & value", "Tests, measured latency, governance, limitations, roadmap, live demo runbook.", GREEN),
    ]
    x = M
    w = (CW - 3 * 0.28) / 4
    for num, title, body, accent in items:
        c = card(slide, x, y, w, 3.55)
        rect(slide, x + 0.001, y, w - 0.002, 0.055, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.24)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.3)
        para(tf, num, size=30, bold=True, color=accent, first=True, space_after=8)
        para(tf, title, size=15.5, bold=True, color=INK, space_after=6)
        para(tf, body, size=11.5, color=MUTED, space_after=0, line_spacing=1.16)
        x += w + 0.28

    strip = card(slide, M, y + 3.82, CW, 0.86, fill=INK, line=None)
    tf = strip.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.3)
    rich(tf, [("Ground rule for this demo:  ", True, WHITE),
              ("every number and every screen in this deck comes from the code in this repository, "
               "measured on a local run. Projections are labelled as projections.", False, "C6CFE2")],
         size=12.5, first=True, space_after=0)
    notes(slide, (
        "Agenda (30s). Four parts. Suggested split: Ankita opens and takes part 1, Santhoshkumar "
        "takes architecture, Vandana drives the live walkthrough, Shubham closes with engineering "
        "quality, limitations and value. Point at the black strip: we deliberately separate "
        "measured facts from projections."))


def slide_problem(d):
    slide, y = d.content(
        "Part 01  ·  Problem", "Manual eligibility review is slow, uneven and hard to audit")
    pains = [
        ("Days to weeks", "A file waits in a queue for a human reviewer before the applicant hears anything.", RED),
        ("Reviewer variance", "Two officers apply the same policy differently; the applicant cannot see why.", AMBER),
        ("Specialist-bound", "Throughput is capped by trained headcount, so volume spikes create backlogs.", VIOLET),
        ("Thin audit trail", "Reasoning lives in notes and inboxes, not in a queryable, timestamped record.", INDIGO),
        ("No self-service", "'Why was I rejected?' and 'what do I fix?' become another support ticket.", CYAN),
    ]
    x = M
    w = (CW - 4 * 0.22) / 5
    for title, body, accent in pains:
        c = card(slide, x, y, w, 2.5)
        rect(slide, x + 0.001, y, w - 0.002, 0.05, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.2)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.26)
        para(tf, title, size=14, bold=True, color=INK, first=True, space_after=6)
        para(tf, body, size=11, color=MUTED, space_after=0, line_spacing=1.16)
        x += w + 0.22

    band = card(slide, M, y + 2.78, CW, 1.42, fill=SURF, line=LINE)
    rect(slide, M + 0.001, y + 2.78, 0.06, 1.42, fill=GREEN)
    tf = band.text_frame
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.2)
    para(tf, "THE OPENING", size=9.5, bold=True, color=GREEN, first=True, space_after=6)
    rich(tf, [("The rules are already deterministic. ", True, INK),
              ("Credit score, age, EMI-to-income ratio and employment stability are arithmetic — "
               "not judgement. Automate the arithmetic, publish the reasoning with the decision, "
               "and route only genuinely borderline files to a human.", False, TEXT)],
         size=13.5, space_after=4)
    para(tf, "That is exactly the boundary our system draws: machine-decided where the policy is "
             "clear, human-decided where it is not, explained in both cases.",
         size=12, color=MUTED, space_after=0)
    notes(slide, (
        "Problem (60s). Lead with the applicant's experience, not the bank's. Five costs of manual "
        "review. Then the pivot: the policy itself is arithmetic — the delay comes from a human "
        "doing arithmetic and then not writing down why. Our system automates the arithmetic and "
        "keeps a record. Hand over to architecture."))


def slide_solution(d):
    slide, y = d.content(
        "Part 01  ·  Solution", "One application, three outputs, no waiting",
        "A Streamlit front end talks to a FastAPI service; agents decide, explain and answer questions.")
    cols = [
        ("The applicant sees", [
            "A single form: personal, financial and loan details",
            "A colour-coded decision within a second",
            "The exact rule-by-rule reasoning behind it",
            "Concrete steps to improve a weak profile",
            "A downloadable PDF assessment report",
        ], INDIGO),
        ("The engine does", [
            "Pydantic validation at the API boundary",
            "Four deterministic rules + a borderline band",
            "EMI estimation and EMI-to-income ratio",
            "Policy evidence retrieved for every decision",
            "An audit line written per request id",
        ], VIOLET),
        ("The assistant adds", [
            "Answers on criteria, process and next steps",
            "Explanations of the applicant's own result",
            "A guard that blocks card / PAN / OTP data",
            "Scope control instead of invented answers",
            "Optional Claude phrasing, rules as fallback",
        ], CYAN),
    ]
    w = (CW - 2 * 0.3) / 3
    x = M
    for title, lines, accent in cols:
        c = card(slide, x, y, w, 3.1)
        rect(slide, x + 0.001, y, w - 0.002, 0.055, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.24)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.26)
        para(tf, title, size=15, bold=True, color=INK, first=True, space_after=10)
        for ln in lines:
            para(tf, ln, size=11.5, color=TEXT, space_after=7, line_spacing=1.12,
                 bullet="—", bullet_color=accent)
        x += w + 0.3

    tf = textbox(slide, M, y + 3.34, CW, 0.5)
    rich(tf, [("Design stance:  ", True, INK),
              ("the decision path is deterministic and testable; the language model is optional and "
               "never authoritative. Pull the API key and every screen in this deck still works.",
               False, MUTED)], size=12, first=True, space_after=0)
    notes(slide, (
        "Solution (60s). Read the three columns as three audiences: applicant, engine, assistant. "
        "The closing line is the one to land — the LLM is a phrasing layer, not the decision maker. "
        "That is why the demo cannot break on stage."))


def slide_features(d):
    slide, y = d.content(
        "Part 01  ·  Functionality", "The complete feature inventory",
        "Everything below is implemented in this repository and demonstrated later in this deck.")
    tiles = [
        ("Guided application form", "Seven inputs across personal, financial and loan sections, with inline help.", INDIGO),
        ("Two-stage validation", "UI checks (name, ranges, EMI vs income) then Pydantic types at the API.", VIOLET),
        ("Deterministic rule engine", "Credit score, age, EMI ratio and employment, each evaluated independently.", CYAN),
        ("Three-way decision", "Eligible / Needs Manual Review / Not Eligible, with a borderline tolerance band.", GREEN),
        ("Credit metrics panel", "Score, estimated new EMI, combined EMI and EMI-to-income ratio.", AMBER),
        ("Reasoning trace", "Per-rule PASSED / FAILED with the value used — shown on screen and in the PDF.", RED),
        ("Recommendation engine", "Targeted improvement steps derived from the rules the applicant failed.", INDIGO),
        ("PDF report", "One-page assessment: applicant, credit report, reasoning, recommendations.", VIOLET),
        ("Policy evidence (RAG)", "Retrieved snippets attached to each decision; FAISS / Pinecone adapters ready.", CYAN),
        ("Support chatbot", "Rules-first answers on criteria and on the applicant's own result.", GREEN),
        ("REST API + OpenAPI", "/process, /chat, /chat/info documented and callable at /docs.", AMBER),
        ("Audit & test suite", f"JSON audit line per request id; {METRICS['tests']} passing unit tests.", RED),
    ]
    cols, rows = 4, 3
    gx, gy = 0.24, 0.24
    w = (CW - (cols - 1) * gx) / cols
    h = (SLIDE_H - y - 0.72 - (rows - 1) * gy) / rows
    for i, (title, body, accent) in enumerate(tiles):
        cx = M + (i % cols) * (w + gx)
        cy = y + (i // cols) * (h + gy)
        feature_tile(slide, cx, cy, w, h, title, body, accent)
    notes(slide, (
        "Feature inventory (45s). Do not read all twelve. Say: 'twelve capabilities, grouped as "
        "capture, decide, explain, distribute, converse and observe' and point at one tile per "
        "group. Tell the audience the walkthrough in part 3 shows each of these on screen."))


def slide_architecture(d):
    slide, y = d.content(
        "Part 02  ·  Architecture", "How a request travels through the system",
        "Two processes, four agents, one audit log. The UI never contains business rules.")

    # Row 1 — request path
    node_w, node_h = 2.42, 1.18
    gap = 0.42
    x = M
    nodes = [
        ("Streamlit UI", ["ui/app.py  ·  :8501", "Form, results, PDF, chat panel"], INDIGO),
        ("FastAPI service", ["service/coordinator_service.py", ":8000  ·  request id + CORS"], VIOLET),
        ("Coordinator agent", ["agents/coordinator.py", "Validate, delegate, compose"], CYAN),
        ("Eligibility agent", ["agents/eligibility_agent.py", "Four rules, one decision"], GREEN),
    ]
    for i, (title, lines, accent) in enumerate(nodes):
        flow_node(slide, x, y, node_w, node_h, title, lines, accent=accent)
        if i < len(nodes) - 1:
            arrow(slide, x + node_w + 0.08, y + node_h / 2 - 0.08, gap - 0.16)
        x += node_w + gap

    tf = textbox(slide, M, y + node_h + 0.12, CW, 0.3)
    para(tf, "HTTP POST /process  →  Pydantic Application  →  rule results  →  decision + reasoning + evidence",
         size=10.5, color=FAINT, first=True, space_after=0)

    # Row 2 — supporting services
    y2 = y + node_h + 0.6
    sw = (CW - 3 * 0.3) / 4
    support = [
        ("RAG retrieval", ["rag_stub.py  ·  rag_adapters.py", "Policy evidence per decision",
                           "FAISS / Pinecone ready"], CYAN),
        ("Chat agent", ["chat_agent.py  ·  chat_knowledge.py", "Guard → intents → FAQ retrieval",
                        "Deterministic, offline-safe"], GREEN),
        ("Claude responder", ["chat_llm.py  ·  llm_client.py", "Opt-in via LOAN_CHAT_LLM=1",
                              "Any failure falls back to rules"], VIOLET),
        ("Audit & logging", ["service/audit.py  ·  logging_config.py", "JSON line per request id",
                             "Chat text never logged"], AMBER),
    ]
    x = M
    for title, lines, accent in support:
        flow_node(slide, x, y2, sw, 1.5, title, lines, fill=SURF, accent=accent)
        x += sw + 0.3

    band = card(slide, M, y2 + 1.78, CW, 0.86, fill=INK, line=None)
    tf = band.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    rich(tf, [("Why split the UI from the service?  ", True, WHITE),
              ("The rules live behind an HTTP boundary, so they are unit-testable, callable by any "
               "other channel, and swappable without touching the front end. The Streamlit app is "
               "one client of the API — the curl call later in this deck is another.", False, "C6CFE2")],
         size=12, first=True, space_after=0)
    notes(slide, (
        "Architecture (90s). Trace one request left to right along the top row, then say the bottom "
        "row is 'everything that hangs off that path'. Emphasise the HTTP boundary: it is why we can "
        "demo the same decision from the browser and from curl, and why the tests do not need a "
        "browser."))


def slide_agents(d):
    slide, y = d.content(
        "Part 02  ·  Agents", "Four agents, one responsibility each",
        "Each agent is a small class with a narrow contract, which is what makes the system testable.")
    agents = [
        ("Coordinator", "agents/coordinator.py", [
            "Parses the payload into a Pydantic Application",
            "Delegates scoring to the eligibility agent",
            "Queries retrieval for supporting evidence",
            "Composes the readable reasoning list",
        ], INDIGO),
        ("Eligibility", "agents/eligibility_agent.py", [
            "Estimates the new EMI and the EMI ratio",
            "Evaluates four rules independently",
            "Applies the borderline tolerance bands",
            "Returns decision + per-rule results",
        ], VIOLET),
        ("Retrieval (RAG)", "agents/rag_stub.py, rag_adapters.py", [
            "Answers a Retriever protocol",
            "Returns policy snippets with ids",
            "Stub today; FAISS / Pinecone adapters exist",
            "Swappable through constructor injection",
        ], CYAN),
        ("Chat", "agents/chat_agent.py, chat_llm.py", [
            "Blocks sensitive identifiers first",
            "Answers result questions from the assessment",
            "Falls back to ranked FAQ retrieval",
            "Optionally rephrases through Claude",
        ], GREEN),
    ]
    w = (CW - 3 * 0.26) / 4
    x = M
    for title, module, lines, accent in agents:
        c = card(slide, x, y, w, 3.0)
        rect(slide, x + 0.001, y, w - 0.002, 0.055, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.22)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.26)
        para(tf, title, size=15, bold=True, color=INK, first=True, space_after=2)
        para(tf, module, size=9.5, color=accent, space_after=10)
        for ln in lines:
            para(tf, ln, size=11, color=MUTED, space_after=7, line_spacing=1.12,
                 bullet="·", bullet_color=accent)
        x += w + 0.26

    tf = textbox(slide, M, y + 3.24, CW, 0.6)
    rich(tf, [("One rule we kept:  ", True, INK),
              ("chat_agent.py never imports chat_llm.py. The dependency runs one way only, so the "
               "chatbot stays importable — and unit-testable — without the anthropic package "
               "installed at all.", False, MUTED)], size=12, first=True, space_after=0)
    notes(slide, (
        "Agents (60s). The point is separation of concerns, not the number four. If asked 'are these "
        "real agents or just classes?' — answer honestly: they are cooperating components with "
        "narrow contracts; only the chat path is model-backed, and even that is optional. The "
        "one-way import rule is a good detail to show engineering discipline."))


def slide_rules(d):
    slide, y = d.content(
        "Part 02  ·  Decision logic", "The rules, exactly as the code applies them",
        "Source of truth: agents/eligibility_agent.py. These are the numbers the demo will produce.")

    rules = [
        ("Credit score", "score > 700", "Strictly greater than — 700 itself does not pass.", INDIGO),
        ("Age", "21 ≤ age ≤ 60", "Both bounds inclusive.", VIOLET),
        ("EMI-to-income", "(existing EMI + new EMI) / income ≤ 0.40", "New EMI is estimated as loan / 12.", CYAN),
        ("Employment", "salaried or govt", "Advisory: strengthens the profile, never blocks alone.", GREEN),
    ]
    w = (CW - 3 * 0.24) / 4
    x = M
    for title, rule, note, accent in rules:
        c = card(slide, x, y, w, 1.62)
        rect(slide, x + 0.001, y, w - 0.002, 0.05, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.2)
        tf.margin_right = Inches(0.16)
        tf.margin_top = Inches(0.2)
        para(tf, title, size=12.5, bold=True, color=INK, first=True, space_after=4)
        para(tf, rule, size=12.5, bold=True, color=accent, space_after=5)
        para(tf, note, size=10, color=MUTED, space_after=0, line_spacing=1.1)
        x += w + 0.24

    y2 = y + 1.9
    tf = textbox(slide, M, y2, CW, 0.3)
    para(tf, "DECISION MATRIX", size=9.5, bold=True, color=INDIGO, first=True, space_after=0)
    y2 += 0.34

    matrix = [
        ("Eligible", "All three critical rules pass", GREEN,
         "Credit > 700 and age in range and EMI ratio ≤ 0.40."),
        ("Needs Manual Review", "A critical rule fails, but inside the borderline band", AMBER,
         "Credit 690–710 or EMI ratio 0.38–0.42 — routed to a human, not refused."),
        ("Not Eligible", "A critical rule fails clearly outside the band", RED,
         "Returned with the failing rule named and improvement steps attached."),
    ]
    rw = (CW - 2 * 0.26) / 3
    x = M
    for title, cond, accent, detail in matrix:
        c = card(slide, x, y2, rw, 1.72, fill=SURF)
        rect(slide, x + 0.001, y2, 0.06, 1.72, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.24)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.2)
        para(tf, title, size=15, bold=True, color=accent, first=True, space_after=5)
        para(tf, cond, size=11.5, bold=True, color=INK, space_after=5, line_spacing=1.1)
        para(tf, detail, size=10.5, color=MUTED, space_after=0, line_spacing=1.12)
        x += rw + 0.26

    band = card(slide, M, y2 + 2.0, CW, 0.62, fill=WHITE, line=LINE)
    tf = band.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.26)
    rich(tf, [("Worked example from the live demo:  ", True, INK),
              ("income ₹95,000 · existing EMI ₹8,000 · loan ₹300,000  →  new EMI ₹25,000  →  "
               "ratio 33,000 / 95,000 = 0.3474  →  with a score of 762, all rules pass  →  Eligible.",
               False, TEXT)], size=11.5, first=True, space_after=0)
    notes(slide, (
        "Rules (75s). This is the slide to be precise on. Call out the strict '>' on 700 — a "
        "score of exactly 700 fails the rule, and the borderline band is what catches it as manual "
        "review rather than a flat refusal. Read the worked example aloud; the same numbers appear "
        "on the next screenshots, so the audience can verify the arithmetic themselves."))


def slide_chat_design(d):
    slide, y = d.content(
        "Part 02  ·  Assistant", "The chatbot answers in layers, and the first layer needs no network",
        "agents/chat_agent.py resolves every question in a fixed order; the model is the last, optional step.")
    steps = [
        ("1  Safety guard", "Card, account, PAN, Aadhaar, OTP or password patterns are detected first. "
         "The message is answered with a warning and forwarded nowhere.", RED),
        ("2  Result intents", "'Why do I need review?', 'what is my EMI ratio?' are answered from the "
         "applicant's own assessment. Missing field → 'no assessment yet', never a guess.", INDIGO),
        ("3  FAQ retrieval", "The knowledge base is ranked with the in-memory vector retriever; a "
         "confidence floor of 0.34 keeps weak matches out and returns a scope reply instead.", VIOLET),
        ("4  Claude (optional)", "With LOAN_CHAT_LLM=1 the retrieved snippets are rephrased "
         "conversationally. Prompt forbids inventing thresholds or promising approval.", GREEN),
    ]
    w = (CW - 3 * 0.26) / 4
    x = M
    for title, body, accent in steps:
        c = card(slide, x, y, w, 2.28)
        rect(slide, x + 0.001, y, w - 0.002, 0.055, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.22)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.24)
        para(tf, title, size=14, bold=True, color=accent, first=True, space_after=7)
        para(tf, body, size=11, color=TEXT, space_after=0, line_spacing=1.16)
        x += w + 0.26

    y2 = y + 2.55
    guarantees = [
        ("Opt-in by flag, not by key", "A stray ANTHROPIC_AUTH_TOKEN in a shell must not silently turn "
         "the form into a billed API caller.", VIOLET),
        ("Failure is invisible to the customer", "API down, rate-limited or refusing → /chat still "
         "returns 200 with the deterministic answer and mode 'rules'.", GREEN),
        ("Privacy by construction", "The applicant's name has no field in AssessmentContext. The audit "
         "log stores message length and matched FAQ ids — never the question text.", CYAN),
    ]
    gw = (CW - 2 * 0.26) / 3
    x = M
    for title, body, accent in guarantees:
        c = card(slide, x, y2, gw, 1.5, fill=SURF)
        rect(slide, x + 0.001, y2, 0.06, 1.5, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.24)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.2)
        para(tf, title, size=12.5, bold=True, color=INK, first=True, space_after=5)
        para(tf, body, size=10.5, color=MUTED, space_after=0, line_spacing=1.14)
        x += gw + 0.26
    notes(slide, (
        "Assistant design (75s). The order of the four layers is the whole argument: safety before "
        "retrieval, exact numbers before language. The three cards below are the guarantees we can "
        "defend under questioning — especially 'opt-in by flag, not by key', which is a real "
        "cost-control decision, and the audit log storing message length rather than text."))


def slide_repo(d):
    slide, y = d.content(
        "Part 02  ·  Codebase", "Repository map and API surface",
        f"{METRICS['modules']} Python modules, {METRICS['tests']} unit tests, no build step.")

    left = card(slide, M, y, CW * 0.53, 4.92, fill=INK, line=None)
    tf = left.text_frame
    tf.margin_left = Inches(0.32)
    tf.margin_top = Inches(0.26)
    para(tf, "PROJECT LAYOUT", size=9.5, bold=True, color=CYAN, first=True, space_after=9)
    tree = [
        ("agents/", "the decision and conversation logic", True),
        ("   coordinator.py", "orchestrates one application", False),
        ("   eligibility_agent.py", "the four rules + decision", False),
        ("   rag_interface.py / rag_adapters.py", "retriever protocol, FAISS, Pinecone", False),
        ("   chat_agent.py / chat_knowledge.py", "guard, intents, FAQ knowledge base", False),
        ("   chat_llm.py / llm_client.py", "optional Claude responder", False),
        ("service/", "the HTTP boundary", True),
        ("   coordinator_service.py", "FastAPI app, three endpoints", False),
        ("   audit.py", "one JSON line per decision", False),
        ("schemas/models.py", "Pydantic request / response models", True),
        ("ui/app.py", "Streamlit form, results, PDF, chat panel", True),
        ("tests/", f"{METRICS['tests']} tests across rules, chat, API, audit", True),
    ]
    for name, desc, top in tree:
        rich(tf, [(name.ljust(2), True, WHITE if top else "9FB0D0"),
                  ("   " + desc, False, "7C8AA8")], size=10.5, space_after=4.5)

    x2 = M + CW * 0.53 + 0.3
    w2 = CW - CW * 0.53 - 0.3
    tf = textbox(slide, x2, y + 0.04, w2, 0.3)
    para(tf, "API SURFACE", size=9.5, bold=True, color=INDIGO, first=True, space_after=0)
    ry = y + 0.42
    endpoints = [
        ("POST /process", "Assess an application. Returns decision, new EMI, EMI ratio, "
         "per-rule reasoning and retrieved evidence.", INDIGO),
        ("POST /chat", "Answer one customer question. Accepts history and the applicant's "
         "assessment context; returns answer, sources and mode.", VIOLET),
        ("GET /chat/info", "Report whether the LLM mode is enabled and list suggested "
         "questions for the UI.", CYAN),
    ]
    for path, desc, accent in endpoints:
        c = card(slide, x2, ry, w2, 1.12, fill=SURF)
        rect(slide, x2 + 0.001, ry, 0.055, 1.12, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.22)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.16)
        para(tf, path, size=13, bold=True, color=accent, first=True, space_after=4)
        para(tf, desc, size=10.5, color=MUTED, space_after=0, line_spacing=1.14)
        ry += 1.24

    c = card(slide, x2, ry + 0.06, w2, 0.72, fill=WHITE, line=LINE)
    tf = c.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.22)
    rich(tf, [("Every request carries an ", False, MUTED), ("X-Request-ID", True, INK),
              (" through the logs and the audit file.", False, MUTED)], size=11, first=True,
         space_after=0)
    notes(slide, (
        "Codebase (45s). Do not read the tree. Say: 'agents hold the logic, service is the HTTP "
        "boundary, schemas is the contract, ui is one client, tests cover all of it.' Then move to "
        "the API surface on the right — three endpoints, and the request id that ties a decision to "
        "its audit line. That id is what we will point at in the observability slide."))


def shot_slide(d, kicker, title, subtitle, image, items, callout_title=None,
               image_frac=0.60, prepared=None):
    """Screenshot on the left, numbered explanation on the right."""
    slide, y = d.content(kicker, title, subtitle)
    img_w = CW * image_frac
    img_h = SLIDE_H - y - 0.72
    path = prepared if prepared else SHOTS / image
    place_image(slide, path, M, y, img_w, img_h)
    callouts(slide, M + img_w + 0.42, y + 0.02, CW - img_w - 0.42, items,
             title=callout_title)
    return slide


def slide_shot_form(d):
    path = prepare("01_landing.png", crop=(0, 0, 1, 0.44))
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 1", "The application form",
        "http://localhost:8501 — one screen, seven inputs, guidance on the left.",
        None, [
            ("Guided sidebar", "How it works, the decision criteria and every field requirement, before the applicant types anything."),
            ("Personal details", "Name, age and employment type, each with inline help text."),
            ("Financial details", "Monthly income, existing EMI and credit score."),
            ("Loan details", "The requested amount, from which the new EMI is estimated."),
            ("Two actions", "Evaluate submits to the API; the assistant panel sits below the guide."),
        ], callout_title="What the applicant sees", prepared=path)
    notes(slide, (
        "Walkthrough 1 (45s). Show the real app here rather than the slide if the projector allows. "
        "Point out that the eligibility criteria are published in the sidebar before submission — "
        "the applicant is never guessing what is being tested. Mention the assistant panel below "
        "the guide; we come back to it."))


def slide_shot_validation(d):
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 2", "Validation happens before any decision",
        "An empty submission never reaches the rule engine.",
        "10_validation_errors.png", [
            ("UI layer", "Name presence and length, age 18–120, income > 0, EMI not negative and not above income, credit score 0–1000, loan > 0, plus sanity ceilings."),
            ("API layer", "Pydantic re-validates types and bounds, and rejects an unknown employment type outright."),
            ("Blocked early", "The request is never sent, so no audit entry and no decision are produced for invalid input."),
            ("Plain messages", "Each failure names the field and the expected range, rather than a generic error."),
        ], callout_title="Two independent layers")
    notes(slide, (
        "Walkthrough 2 (40s). Deliberately click Evaluate on an empty form during the live demo — it "
        "shows the guard rails and takes five seconds. The message to land: validation is duplicated "
        "on purpose, because the API has clients other than this UI."))


def slide_shot_eligible(d):
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 3", "An eligible decision, with the arithmetic shown",
        "Applicant: 34, salaried, income ₹95,000, existing EMI ₹8,000, score 762, loan ₹300,000.",
        None, [
            ("Colour-coded verdict", "Green for Eligible, amber for manual review, red for refusal — the same three colours in the UI and the PDF."),
            ("Credit score", "762 / 1000, flagged GOOD because it clears the 700 threshold."),
            ("Estimated new EMI", "₹25,000 — the requested ₹300,000 spread over twelve months."),
            ("EMI-to-income ratio", "33,000 / 95,000 = 34.7%, inside the 40% limit."),
            ("Report download", "The PDF is generated in the same run, ready before the applicant asks."),
        ], callout_title="Reading the result",
        prepared=prepare("03_result_eligible.png", crop=(0, 0, 1, 0.955)))
    notes(slide, (
        "Walkthrough 3 (60s). This is the money slide. Do the arithmetic out loud: 8,000 existing "
        "plus 25,000 new is 33,000 against 95,000 income, which is 34.7% — under 40, so it passes. "
        "The audience should be able to check every number we display. Note the PDF is already "
        "generated, not queued."))


def slide_shot_reasoning(d):
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 4", "Every decision ships with its reasoning and its evidence",
        "The same four lines appear on screen, in the PDF and in the assistant's answers.",
        "04_reasoning_and_recommendations.png", [
            ("Rule-by-rule trace", "Each rule reports PASSED or FAILED, the value used and the policy sentence behind it."),
            ("No black box", "Nothing is aggregated into an opaque score — the applicant sees the four independent checks."),
            ("Recommendations", "Generated only for the rules that failed, so a strong profile is told 'no improvements needed'."),
            ("Policy references", "Retrieved snippets are attached to the decision and expandable, with their source ids."),
        ], callout_title="Explainability")
    notes(slide, (
        "Walkthrough 4 (45s). Explainability is the differentiator against a black-box score. Say: "
        "'the same wording is reused in three places — screen, PDF and chatbot — because they all "
        "read from one function.' That is why the assistant can never contradict the page."))


def slide_shot_review(d):
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 5", "The borderline case routes to a human",
        "Applicant: 38, self-employed, income ₹70,000, existing EMI ₹4,000, score 695, loan ₹300,000.",
        None, [
            ("Two near misses", "Score 695 sits in the 690–710 band; the EMI ratio of 41.4% sits in the 0.38–0.42 band."),
            ("Not a refusal", "Both failures are borderline, so the decision is Needs Manual Review rather than Not Eligible."),
            ("Amber everywhere", "The badge, the metrics and the PDF all switch to amber for this state."),
            ("Human in the loop", "The applicant is told a loan officer will review the case, and why it was escalated."),
        ], callout_title="Why amber, not red",
        prepared=prepare("08_result_manual_review.png", crop=(0, 0, 1, 0.955)))
    notes(slide, (
        "Walkthrough 5 (50s). This is the slide that answers 'is this just a hard cut-off?'. No: "
        "there is a deliberate tolerance band, and inside it the system defers to a human instead of "
        "refusing. Contrast 695 against the 700 rule — five points should not be an automatic "
        "rejection, and it isn't."))


def slide_shot_not_eligible(d):
    slide, y = d.content(
        "Part 03  ·  Walkthrough 6", "A clear refusal still leaves the applicant with a plan",
        "Applicant: 29, other employment, income ₹50,000, existing EMI ₹10,000, score 640, loan ₹600,000.")
    half = (CW - 0.34) / 2
    img_h = SLIDE_H - y - 2.16
    place_image(slide, prepare("09_result_not_eligible.png", crop=(0, 0, 1, 0.955)),
                M, y, half, img_h)
    place_image(slide, SHOTS / "09b_not_eligible_recommendations.png",
                M + half + 0.34, y, half, img_h)

    ty = y + img_h + 0.18
    cols = [
        ("What failed", "Score 640 is far below 700 and the EMI ratio is 120% — both well outside the "
         "borderline bands, so the decision is Not Eligible.", RED),
        ("What is offered", "Four targeted actions: raise the score above 700, dispute report errors, "
         "cut card utilisation below 30%, avoid new accounts.", INDIGO),
        ("Why it matters", "A refusal with a route back is a retained customer. The same list goes "
         "into the PDF and drives the assistant's advice.", GREEN),
    ]
    cw = (CW - 2 * 0.28) / 3
    x = M
    for title, body, accent in cols:
        c = card(slide, x, ty, cw, 1.16, fill=SURF)
        rect(slide, x + 0.001, ty, 0.055, 1.16, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.22)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.16)
        para(tf, title, size=12.5, bold=True, color=INK, first=True, space_after=4)
        para(tf, body, size=10.5, color=MUTED, space_after=0, line_spacing=1.14)
        x += cw + 0.28
    notes(slide, (
        "Walkthrough 6 (50s). Show that a 120% EMI ratio is an obvious refusal — the request is "
        "simply unaffordable at that income. Then pivot to the recommendations: the system never "
        "ends on 'no'. Recommendations are generated from the failed rules, so they are specific, "
        "not boilerplate."))


def slide_shot_pdf(d):
    path = prepare("14_pdf_report_p1.png", crop=(0, 0, 1, 0.55))
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 7", "The PDF assessment report",
        "Generated in-process with ReportLab at the moment of the decision — no external service.",
        None, [
            ("Traceable header", "Timestamp, applicant name and a short report id for support conversations."),
            ("Colour-coded verdict", "The same green / amber / red vocabulary as the screen."),
            ("Applicant and credit sections", "Inputs echoed back, plus score status, estimated EMI and the ratio."),
            ("Reasoning and next steps", "The four rule lines, then the recommendations — or a clean bill of health."),
            ("Disclaimer", "Every report states that the assessment is automated and subject to review."),
        ], callout_title="One page, everything decided", prepared=path, image_frac=0.52)
    notes(slide, (
        "Walkthrough 7 (40s). Download the PDF live — it takes a second and proves it is real. The "
        "report is the artefact the applicant keeps and the officer receives, which is why the "
        "reasoning and the disclaimer both belong in it. Known cosmetic issue: the rupee glyph is "
        "missing from the built-in PDF font, so amounts show a placeholder box; the fix is to "
        "register a Unicode font in generate_pdf()."))


def slide_shot_chat(d):
    path = prepare("06_chat_sidebar.png", columns=2)
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 8", "The assistant explains this applicant's own result",
        "The panel sits in the sidebar and receives the assessment — never the applicant's name.",
        None, [
            ("'Why am I eligible?'", "Answered from the actual rule results, quoting the same four checks shown on the page."),
            ("'What is my EMI ratio?'", "34.7% with the explanation of how it is composed — the number comes from the assessment, not the model."),
            ("'What documents will I need?'", "A process question, answered from the FAQ knowledge base."),
            ("Sources shown", "Each answer lists the FAQ entries it drew on, expandable for the full text."),
            ("Mode badge", "'Instant answers from our policy guide' — this run needed no API key at all."),
        ], callout_title="Result-aware answers", prepared=path, image_frac=0.44)
    notes(slide, (
        "Walkthrough 8 (60s). Ask the questions live, in this order. The key claim: the numbers in "
        "the answers are read from the assessment, so they cannot drift from the page. Point at the "
        "source expanders — every answer is attributable. And note the mode badge: this whole "
        "conversation ran with no API key and no internet."))


def slide_shot_chat_safety(d):
    path = prepare("07_chat_safety.png", columns=2)
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 9", "Two things the assistant refuses to do",
        "Sensitive data is stopped at the door, and out-of-scope questions are declined, not guessed.",
        None, [
            ("Sensitive input blocked", "A card number in the message triggers the guard: the applicant is warned and the text is forwarded nowhere — not to retrieval, not to any API."),
            ("Never logged", "The audit line records the message length and matched FAQ ids. The question text itself is never written to disk."),
            ("Scope control", "An off-topic question gets an honest 'I can only help with…' plus suggestions, instead of a fabricated answer."),
            ("Confidence floor", "Retrieval below 0.34 confidence is treated as out of scope by design."),
        ], callout_title="Guard rails", prepared=path, image_frac=0.44)
    notes(slide, (
        "Walkthrough 9 (50s). Type a fake card number live — it is the most memorable moment in the "
        "demo. Two guarantees: the data goes nowhere, and the log keeps a length instead of the "
        "text. Then the weather question: refusing to answer is a feature. A chatbot that invents "
        "loan thresholds is a compliance problem."))


def slide_shot_api(d):
    path = prepare("12_api_process_endpoint.png", crop=(0, 0, 1, 0.62))
    slide = shot_slide(
        d, "Part 03  ·  Walkthrough 10", "The same decision, straight from the API",
        "http://localhost:8000/docs — FastAPI generates the OpenAPI schema and this console from the code.",
        None, [
            ("Self-documenting", "Endpoint descriptions, request schema and response codes come from the Pydantic models and docstrings."),
            ("Try it out", "The decision can be exercised from the browser, with no UI involved."),
            ("Typed contract", "Unknown employment types or out-of-range values return 422 with the offending field."),
            ("Integration ready", "Any channel — mobile app, core banking, batch job — can call the same endpoint."),
        ], callout_title="Why this matters", prepared=path, image_frac=0.60)
    notes(slide, (
        "Walkthrough 10 (40s). This is the slide for a technical examiner. The UI is one client; the "
        "contract is the API. Offer to run the curl command from the next slide if they want to see "
        "it outside the browser."))


def slide_observability(d):
    path = prepare("13_audit_trail.png", crop=(0, 0, 1, 0.945))
    slide = shot_slide(
        d, "Part 04  ·  Observability", "Every decision leaves a record, and the suite proves the rules",
        "A real request, the audit lines it produced, and the test run — captured from this machine.",
        None, [
            ("Request in, decision out", "The JSON response carries the decision, the EMI figures, the reasoning and the evidence ids."),
            ("One audit line per decision", "logs/audit.log stores request id, UTC timestamp, an input summary, the decision and the evidence ids — as JSON lines, greppable."),
            ("Correlated logs", "An X-Request-ID supplied by the caller is reused, so a UI click, the service log and the audit line share one identifier."),
            (f"{METRICS['tests']} tests, all passing", "Rules, chatbot intents, the LLM fallback path, the API endpoints and audit writing are all covered."),
        ], callout_title="What we can prove after the fact", prepared=path, image_frac=0.58)
    notes(slide, (
        "Observability (50s). Say plainly: an auditor's question is 'why did this applicant get this "
        "answer on this date?' — and the audit log plus the reasoning list answers it. Note what is "
        "deliberately absent from the chat audit lines: the question text. Close on the test count "
        "and offer to run pytest live; it finishes in about a second."))


def slide_quality(d):
    slide, y = d.content(
        "Part 04  ·  Engineering quality", "Measured, not estimated",
        "Local run on the development machine: single Uvicorn worker, 60 sequential requests, "
        "reproducible with pytest -q and docs/capture_screenshots.py.")
    tiles = [
        (f"{METRICS['tests']}", "unit tests passing", INDIGO),
        (METRICS["p50"], "median /process latency", VIOLET),
        (METRICS["p95"], "95th percentile latency", CYAN),
        (METRICS["chat_p50"], "median /chat latency (rules mode)", GREEN),
        ("100%", "repeatable decisions", AMBER),
        ("0", "external calls per decision", RED),
    ]
    w = (CW - 5 * 0.22) / 6
    x = M
    for value, label, accent in tiles:
        chip(slide, x, y, w, 1.28, label, value, accent)
        x += w + 0.22

    y2 = y + 1.56
    props = [
        ("Deterministic by construction", "The decision path contains no sampling and no model call. "
         "The same application always yields the same decision, which is what makes the rules "
         "unit-testable and the outcome auditable.", INDIGO),
        ("Degrades instead of failing", "If the Claude responder is unreachable, rate-limited or "
         "declines, /chat still returns 200 with the deterministic answer. If the backend is down, "
         "the UI shows a clear message rather than a stack trace.", GREEN),
        ("Honest about scope", "These are development-machine numbers on a single worker, not a "
         "load-tested production claim. We report what we measured and label the rest as "
         "projection.", AMBER),
    ]
    pw = (CW - 2 * 0.28) / 3
    x = M
    for title, body, accent in props:
        c = card(slide, x, y2, pw, 2.05)
        rect(slide, x + 0.001, y2, pw - 0.002, 0.055, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.24)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.26)
        para(tf, title, size=14.5, bold=True, color=INK, first=True, space_after=8)
        para(tf, body, size=11.5, color=MUTED, space_after=0, line_spacing=1.18)
        x += pw + 0.28
    notes(slide, (
        "Quality (50s). Read the six tiles as a set: fast, covered, repeatable. Then the third card "
        "is the one that earns credibility with an examiner — we are explicit that these are local "
        "numbers on one worker. If asked for production throughput, say we have not load-tested and "
        "it is the next step in the roadmap."))


def slide_governance(d):
    slide, y = d.content(
        "Part 04  ·  Governance", "Controls in place, and limitations we are open about",
        "Knowing the boundary of a prototype is part of presenting it.")
    left_w = (CW - 0.34) / 2
    c = card(slide, M, y, left_w, 4.3)
    rect(slide, M + 0.001, y, left_w - 0.002, 0.055, fill=GREEN)
    tf = c.text_frame
    tf.margin_left = Inches(0.28)
    tf.margin_right = Inches(0.24)
    tf.margin_top = Inches(0.28)
    para(tf, "Controls implemented", size=16, bold=True, color=INK, first=True, space_after=10)
    for head, body in [
        ("Validation at both layers", "UI ranges and Pydantic types; unknown employment values rejected."),
        ("Transparent thresholds", "Published in the sidebar and restated in every decision."),
        ("Human escalation path", "Borderline cases are routed to review rather than refused."),
        ("Audit trail", "One JSON line per decision, keyed by request id."),
        ("Sensitive-data guard", "Card, PAN, Aadhaar, OTP patterns blocked before any processing."),
        ("Data minimisation", "The chat path never receives the applicant's name; chat text is never logged."),
        ("Model containment", "The LLM only rephrases retrieved facts, and is off by default."),
    ]:
        rich(tf, [(head + " — ", True, INK), (body, False, MUTED)], size=11.5, space_after=7)

    x2 = M + left_w + 0.34
    c = card(slide, x2, y, left_w, 4.3)
    rect(slide, x2 + 0.001, y, left_w - 0.002, 0.055, fill=AMBER)
    tf = c.text_frame
    tf.margin_left = Inches(0.28)
    tf.margin_right = Inches(0.24)
    tf.margin_top = Inches(0.28)
    para(tf, "Known limitations of this prototype", size=16, bold=True, color=INK, first=True,
         space_after=10)
    for head, body in [
        ("EMI is a placeholder formula", "New EMI = loan / 12, with no interest rate or tenure. Real amortisation is required before production use."),
        ("Retrieval is a stub", "Three in-repo policy snippets. The FAISS and Pinecone adapters exist but are not wired to a real policy corpus."),
        ("No persistence or auth", "Nothing is stored beyond the audit log; there is no login, and no role separation for officers."),
        ("Not a credit bureau", "The score is an input the applicant supplies; nothing is verified against an external source."),
        ("Single-process demo", "Local Uvicorn and Streamlit; no TLS, no rate limiting, no horizontal scaling yet."),
    ]:
        rich(tf, [(head + " — ", True, INK), (body, False, MUTED)], size=11.5, space_after=8)
    notes(slide, (
        "Governance (60s). Present both columns at the same pace — the limitations column is a "
        "strength, not an apology. If an examiner asks 'could a bank deploy this tomorrow?', the "
        "honest answer is on the right: the decision framework is sound, but EMI maths, a real "
        "policy corpus, persistence, auth and verification are prerequisites. Naming them shows we "
        "understand the domain."))


def slide_value(d):
    slide, y = d.content(
        "Part 04  ·  Value", "Where the value comes from — and what we have not proven",
        "The left column is demonstrated in this deck. The right column is an illustrative model "
        "with its assumptions stated; it is not a measurement.")

    left_w = CW * 0.475
    c = card(slide, M, y, left_w, 3.95, fill=SURF)
    rect(slide, M + 0.001, y, left_w - 0.002, 0.055, fill=GREEN)
    tf = c.text_frame
    tf.margin_left = Inches(0.28)
    tf.margin_top = Inches(0.26)
    para(tf, "DEMONSTRATED IN THIS DECK", size=9.5, bold=True, color=GREEN, first=True,
         space_after=10)
    for head, body in [
        ("Decision time collapses", f"A complete assessment returns in about {METRICS['p50']}, replacing a queue wait."),
        ("Uniform application of policy", "The same input always produces the same decision and the same reasoning."),
        ("Explanations at zero marginal cost", "Reasoning, recommendations and a PDF are produced with the decision."),
        ("Deflected support contact", "Criteria and result questions are answered in the app, without a ticket."),
        ("Reviewer effort focused", "Only borderline files reach a human, with the reason for escalation attached."),
    ]:
        rich(tf, [(head + " — ", True, INK), (body, False, MUTED)], size=11.5, space_after=8)

    x2 = M + left_w + 0.32
    rw = CW - left_w - 0.32
    c = card(slide, x2, y, rw, 3.95)
    rect(slide, x2 + 0.001, y, rw - 0.002, 0.055, fill=AMBER)
    tf = c.text_frame
    tf.margin_left = Inches(0.28)
    tf.margin_top = Inches(0.26)
    para(tf, "ILLUSTRATIVE MODEL — NOT MEASURED", size=9.5, bold=True, color=AMBER, first=True,
         space_after=8)
    para(tf, "If a lender received 2,000 applications a month and a manual first-pass review took "
             "20 minutes at ₹400 per hour, then automating the clear-cut cases would free roughly:",
         size=11.5, color=TEXT, space_after=10, line_spacing=1.16)
    for head, body in [
        ("~560 reviewer hours a month", "assuming 85% of files are not borderline"),
        ("~₹2.7 lakh a month in first-pass effort", "at the stated rate, before any quality gain"),
        ("Same-session answers", "instead of a multi-day wait for the applicant"),
    ]:
        rich(tf, [(head, True, INK), ("  ·  " + body, False, MUTED)], size=11.5, space_after=7)
    para(tf, "Every figure above is arithmetic on assumptions we chose, shown so it can be "
             "challenged. We have not run this system against real applications, so we make no "
             "accuracy, ROI or throughput claim.",
         size=10.5, color=AMBER, space_after=0, line_spacing=1.14)

    band = card(slide, M, y + 4.2, CW, 0.62, fill=INK, line=None)
    tf = band.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.3)
    rich(tf, [("If you take one thing from this section:  ", True, WHITE),
              ("we separate what we measured from what we modelled, and we label both.",
               False, "C6CFE2")], size=12, first=True, space_after=0)
    notes(slide, (
        "Value (60s). Be disciplined here. Left column: things this deck actually shows. Right "
        "column: a transparent model with the assumptions on screen — 2,000 applications, 20 "
        "minutes, ₹400 an hour, 85% clear-cut. Invite challenge to the assumptions; that is the "
        "point of showing them. Explicitly say we make no accuracy or ROI claim, because we have "
        "not tested against real applications."))


def slide_roadmap(d):
    slide, y = d.content(
        "Part 04  ·  Roadmap", "What we would build next, in order",
        "Ordered by what blocks production use, not by what is most interesting to build.")
    stages = [
        ("Next", "Make the maths real", [
            "Proper amortisation: rate, tenure, schedule",
            "Configurable thresholds instead of constants",
            "Golden-file tests over a scenario matrix",
        ], INDIGO),
        ("Then", "Make the knowledge real", [
            "Index the actual policy corpus",
            "Wire the FAISS / Pinecone adapter in place of the stub",
            "Cite document and clause in every decision",
        ], VIOLET),
        ("Then", "Make it operable", [
            "PostgreSQL persistence and case history",
            "Authentication and an officer review queue",
            "Containerised deploy, TLS, rate limiting",
        ], CYAN),
        ("Later", "Make it verifiable", [
            "Bureau integration for score verification",
            "Document upload and checks",
            "Load testing and monitoring dashboards",
        ], GREEN),
    ]
    w = (CW - 3 * 0.26) / 4
    x = M
    for tag, title, items, accent in stages:
        c = card(slide, x, y, w, 3.05)
        rect(slide, x + 0.001, y, w - 0.002, 0.055, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.24)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.26)
        para(tf, tag.upper(), size=9.5, bold=True, color=accent, first=True, space_after=6)
        para(tf, title, size=15, bold=True, color=INK, space_after=10)
        for it in items:
            para(tf, it, size=11.5, color=MUTED, space_after=8, line_spacing=1.14,
                 bullet="—", bullet_color=accent)
        x += w + 0.26

    tf = textbox(slide, M, y + 3.28, CW, 0.5)
    rich(tf, [("Note the ordering:  ", True, INK),
              ("the EMI formula and the policy corpus come before any new feature, because a "
               "correct-looking decision built on a placeholder calculation is the most dangerous "
               "state this system could be in.", False, MUTED)], size=12, first=True, space_after=0)
    notes(slide, (
        "Roadmap (40s). The ordering is the argument: correctness of the maths first, real policy "
        "knowledge second, operability third, external verification last. If asked 'why not add "
        "more agents or a fancier model?' — because neither fixes the loan / 12 placeholder."))


def slide_runbook(d):
    slide, y = d.content(
        "Part 04  ·  Live demo", "Runbook for the demonstration",
        "Five minutes, four scenarios, in this order. Both services must already be running.")

    c = card(slide, M, y, CW * 0.42, 2.05, fill=INK, line=None)
    tf = c.text_frame
    tf.margin_left = Inches(0.28)
    tf.margin_top = Inches(0.22)
    para(tf, "BEFORE YOU PRESENT", size=9.5, bold=True, color=CYAN, first=True, space_after=8)
    for cmd in [
        "python -m uvicorn service.coordinator_service:app --port 8000",
        "streamlit run ui/app.py",
        "pytest -q            # 43 passed",
        "open http://localhost:8501  and  :8000/docs",
    ]:
        para(tf, cmd, size=10.5, color="9FB0D0", space_after=6, font="Consolas")

    x2 = M + CW * 0.42 + 0.3
    w2 = CW - CW * 0.42 - 0.3
    c = card(slide, x2, y, w2, 2.05, fill=SURF)
    rect(slide, x2 + 0.001, y, 0.06, 2.05, fill=AMBER)
    tf = c.text_frame
    tf.margin_left = Inches(0.26)
    tf.margin_top = Inches(0.22)
    para(tf, "TWO THINGS TO AVOID ON STAGE", size=9.5, bold=True, color=AMBER, first=True,
         space_after=8)
    rich(tf, [("Do not use 'Clear Form' between scenarios. ", True, INK),
              ("Streamlit keeps widget state by key, so the fields do not actually reset — reload "
               "the page (F5) instead, or simply type over the values.", False, MUTED)],
         size=11.5, space_after=7)
    rich(tf, [("Do not enable the LLM mode for the demo. ", True, INK),
              ("Rules mode needs no key and no network, and answers in about five milliseconds. "
               "Mention the Claude mode; do not depend on it.", False, MUTED)], size=11.5,
         space_after=0)

    y2 = y + 2.32
    steps = [
        ("1  Eligible", "Ankita Vyas · 34 · salaried\n95,000 income · 8,000 EMI\nscore 762 · loan 300,000",
         "Green verdict, 34.7% ratio, download the PDF.", GREEN),
        ("2  Manual review", "Shubham Kumar · 38 · self-employed\n70,000 income · 4,000 EMI\nscore 695 · loan 300,000",
         "Amber verdict — explain the borderline bands.", AMBER),
        ("3  Not eligible", "Vandana H K · 29 · other\n50,000 income · 10,000 EMI\nscore 640 · loan 600,000",
         "Red verdict, 120% ratio, read the four recommendations.", RED),
        ("4  Assistant", "Ask: 'Why am I eligible?'\nthen 'What is my EMI ratio?'\nthen paste a fake card number",
         "Result-aware answers, then the safety guard fires.", INDIGO),
    ]
    w = (CW - 3 * 0.24) / 4
    x = M
    for title, inputs, outcome, accent in steps:
        c = card(slide, x, y2, w, 2.28)
        rect(slide, x + 0.001, y2, w - 0.002, 0.055, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.22)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.24)
        para(tf, title, size=13.5, bold=True, color=accent, first=True, space_after=7)
        for line in inputs.split("\n"):
            para(tf, line, size=10.5, color=TEXT, space_after=2, line_spacing=1.08,
                 font="Consolas")
        para(tf, outcome, size=10.5, bold=True, color=INK, space_before=7, space_after=0,
             line_spacing=1.12)
        x += w + 0.24
    notes(slide, (
        "Runbook. Keep this slide up while driving the app, or print it. Order matters: eligible "
        "first so the happy path lands, then borderline, then refusal, then the assistant on top of "
        "the last result. The two warnings are from real behaviour we hit while rehearsing: the "
        "Clear Form button does not reset Streamlit widget state, and LLM mode adds latency and a "
        "dependency you do not need on stage."))


def slide_close(d):
    slide = d.dark()
    gradient_band(slide, 0, 0, SLIDE_W, 0.085, INDIGO, VIOLET)
    gradient_band(slide, 0, SLIDE_H - 0.085, SLIDE_W, 0.085, VIOLET, INDIGO)

    tf = textbox(slide, M + 0.25, 1.15, 9.6, 0.35)
    para(tf, "THANK YOU  ·  QUESTIONS WELCOME", size=11, bold=True, color=CYAN, first=True,
         space_after=0)
    tf = textbox(slide, M + 0.25, 1.6, 10.4, 1.5)
    para(tf, "A decision you can explain,\nin the time it takes to click.", size=36, bold=True,
         color=WHITE, first=True, space_after=0, line_spacing=1.1)

    summary = [
        ("Deterministic decisions", "Four published rules, a borderline band, a human escalation path.", INDIGO),
        ("Explained by default", "Reasoning, recommendations, evidence and a PDF with every result.", VIOLET),
        ("A safe assistant", "Rules-first answers, sensitive data blocked, scope honestly limited.", CYAN),
        ("Auditable and tested", f"A JSON line per decision, {METRICS['tests']} passing tests.", GREEN),
    ]
    w = (CW - 3 * 0.26) / 4
    x = M
    y = 3.35
    for title, body, accent in summary:
        c = card(slide, x, y, w, 1.42, fill=INK_SOFT, line=None)
        rect(slide, x + 0.001, y, w - 0.002, 0.05, fill=accent)
        tf = c.text_frame
        tf.margin_left = Inches(0.22)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.2)
        para(tf, title, size=13, bold=True, color=WHITE, first=True, space_after=5)
        para(tf, body, size=10.5, color="A9B4CC", space_after=0, line_spacing=1.14)
        x += w + 0.26

    tf = textbox(slide, M, 5.35, CW, 0.35)
    para(tf, "PRESENTED BY", size=9.5, bold=True, color=FAINT, first=True, space_after=0)
    w = (CW - 3 * 0.26) / 4
    x = M
    roles = ["Problem & solution", "Architecture & design", "Live walkthrough",
             "Engineering & value"]
    for name, role in zip(TEAM, roles):
        tf = textbox(slide, x, 5.72, w, 0.7)
        para(tf, name, size=14, bold=True, color=WHITE, first=True, space_after=3)
        para(tf, role, size=10.5, color=CYAN, space_after=0)
        x += w + 0.26

    tf = textbox(slide, M, 6.45, CW, 0.3)
    para(tf, f"Loan Eligibility AI  ·  Streamlit + FastAPI + Pydantic + RAG retrieval  ·  {DECK_DATE}",
         size=10, color=FAINT, first=True, space_after=0)
    d.footer(slide, dark=True)
    notes(slide, (
        "Close (30s). Restate the four summary cards as one sentence: deterministic, explained, "
        "safe, auditable. The presenter split under the names is a suggestion — adjust it to who "
        "actually speaks. Then open for questions; the likely ones are the EMI formula, whether "
        "this is 'really' agentic, and what happens when the LLM is enabled. Answers to all three "
        "are in parts 2 and 4."))


def build():
    d = Deck()
    slide_title(d)
    slide_agenda(d)

    d.section("01", "Problem & Solution", "Why manual eligibility review does not scale, "
              "and what we built instead.", f"{TEAM[0]}")
    slide_problem(d)
    slide_solution(d)
    slide_features(d)

    d.section("02", "Architecture & Design", "The request path, the agents, the rules and the "
              "assistant's layers.", f"{TEAM[1]}")
    slide_architecture(d)
    slide_agents(d)
    slide_rules(d)
    slide_chat_design(d)
    slide_repo(d)

    d.section("03", "Live Walkthrough", "Every screen of the running application, captured from "
              "localhost.", f"{TEAM[2]}")
    slide_shot_form(d)
    slide_shot_validation(d)
    slide_shot_eligible(d)
    slide_shot_reasoning(d)
    slide_shot_review(d)
    slide_shot_not_eligible(d)
    slide_shot_pdf(d)
    slide_shot_chat(d)
    slide_shot_chat_safety(d)
    slide_shot_api(d)

    d.section("04", "Engineering & Value", "Observability, measured quality, governance, "
              "limitations and next steps.", f"{TEAM[3]}")
    slide_observability(d)
    slide_quality(d)
    slide_governance(d)
    slide_value(d)
    slide_roadmap(d)
    slide_runbook(d)
    slide_close(d)

    d.prs.save(OUTFILE)
    print(f"wrote {OUTFILE.relative_to(ROOT)}  ({len(d.prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    build()
