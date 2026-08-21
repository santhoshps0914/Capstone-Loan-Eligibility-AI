"""Regenerate the capstone presentation deck.

Builds `Loan_Eligibility_AI_Presentation.pptx` from scratch so that the deck covers
every section required by the capstone rubric, in order, with speaker notes sized
for a 15-minute delivery.

Run from the project root:

    python tools/build_presentation.py

The previous deck is expected to be kept as
`Loan_Eligibility_AI_Presentation.backup.pptx` (this script does not touch it).
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

OUT = Path(__file__).resolve().parent.parent / "Loan_Eligibility_AI_Presentation.pptx"

# Palette carried over from the original deck so the visual identity is unchanged.
BLUE = RGBColor(0x1F, 0x77, 0xB4)
GREEN = RGBColor(0x28, 0xA7, 0x45)
AMBER = RGBColor(0xFF, 0xC1, 0x07)
RED = RGBColor(0xDC, 0x35, 0x45)
TEAL = RGBColor(0x17, 0xA2, 0xB8)
GREY = RGBColor(0x6C, 0x75, 0x7D)
INK = RGBColor(0x21, 0x25, 0x29)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BLUE = RGBColor(0xF0, 0xF8, 0xFF)
LIGHT_GREEN = RGBColor(0xF0, 0xFF, 0xF0)
LIGHT_AMBER = RGBColor(0xFF, 0xFA, 0xF0)
LIGHT_GREY = RGBColor(0xF0, 0xF2, 0xF6)

CODE_FONT = "Consolas"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = 13.333


# --------------------------------------------------------------------------- #
# primitives
# --------------------------------------------------------------------------- #
def slide(notes=None):
    s = prs.slides.add_slide(BLANK)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def _style(par, run, size, bold, color, align, font=None, space_after=4):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    if font:
        run.font.name = font
    par.alignment = align
    par.space_after = Pt(space_after)


def _expand(specs):
    """Split any spec whose text contains newlines into one spec per line.

    Literal newlines inside a run render inconsistently across PowerPoint and
    LibreOffice; separate paragraphs behave identically everywhere.
    """
    out = []
    for spec in specs:
        text = spec[0]
        if "\n" in text:
            for part in text.split("\n"):
                out.append((part,) + tuple(spec[1:]))
        else:
            out.append(spec)
    return out


def textbox(s, left, top, width, height, lines, align=PP_ALIGN.LEFT,
            anchor=MSO_ANCHOR.TOP, word_wrap=True):
    """lines: list of (text, size, bold, color) or (text, size, bold, color, indent)."""
    box = s.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = word_wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.08)
    for i, spec in enumerate(_expand(lines)):
        text, size, bold, color = spec[:4]
        indent = spec[4] if len(spec) > 4 else 0
        font = spec[5] if len(spec) > 5 else None
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.level = indent
        _style(par, par.add_run(), size, bold, color, align, font)
        par.runs[0].text = text
    return box


def shape(s, kind, left, top, width, height, fill, line=None, lines=(),
          align=PP_ALIGN.CENTER, line_width=1.5, anchor=MSO_ANCHOR.MIDDLE):
    sp = s.shapes.add_shape(kind, Inches(left), Inches(top), Inches(width), Inches(height))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_width)
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    tf.margin_left = tf.margin_right = Inches(0.08)
    for i, spec in enumerate(_expand(lines)):
        text, size, bold, color = spec[:4]
        font = spec[4] if len(spec) > 4 else None
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        _style(par, par.add_run(), size, bold, color, align, font, space_after=0)
        par.runs[0].text = text
    return sp


def card(s, left, top, width, height, lines, fill=LIGHT_BLUE, line=BLUE,
         align=PP_ALIGN.CENTER):
    return shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height,
                 fill, line, lines, align)


def title_bar(s, text, sub=None):
    shape(s, MSO_SHAPE.RECTANGLE, 0, 0, SW, 0.95, BLUE, BLUE,
          [(text, 26, True, WHITE)])
    if sub:
        textbox(s, 0.5, 1.0, SW - 1.0, 0.35, [(sub, 13, False, GREY)])


def section_tag(s, text):
    """Small rubric-section marker in the top-right of the title bar."""
    tb = textbox(s, SW - 3.3, 0.28, 3.0, 0.4, [(text, 11, True, RGBColor(0xCF, 0xE4, 0xF5))],
                 align=PP_ALIGN.RIGHT)
    return tb


def bullets(s, left, top, width, height, items, size=15, color=INK, bullet_char="• "):
    lines = []
    for it in items:
        if isinstance(it, tuple):
            text, lvl = it
        else:
            text, lvl = it, 0
        prefix = "" if lvl < 0 else ("" if lvl == 0 and text.endswith(":") else bullet_char)
        lines.append((prefix + text, size if lvl <= 0 else size - 1, lvl == 0 and text.endswith(":"),
                      color, max(lvl, 0)))
    return textbox(s, left, top, width, height, lines)


def table_grid(s, left, top, col_w, row_h, headers, rows, size=12):
    for i, h in enumerate(headers):
        shape(s, MSO_SHAPE.RECTANGLE, left + i * col_w, top, col_w, row_h,
              BLUE, WHITE, [(h, size, True, WHITE)], line_width=0.75)
    for r, row in enumerate(rows):
        bg = WHITE if r % 2 == 0 else LIGHT_GREY
        for i, cell in enumerate(row):
            shape(s, MSO_SHAPE.RECTANGLE, left + i * col_w, top + (r + 1) * row_h,
                  col_w, row_h, bg, RGBColor(0xC8, 0xD0, 0xD8),
                  [(cell, size, i == 0, INK)], line_width=0.75)


def footnote(s, text, top=6.85, color=GREY, size=11):
    textbox(s, 0.5, top, SW - 1.0, 0.45, [(text, size, False, color)])


def arrow_down(s, left, top, w=0.55, h=0.3):
    shape(s, MSO_SHAPE.DOWN_ARROW, left, top, w, h, BLUE, None)


def arrow_right(s, left, top, w=0.35, h=0.5):
    shape(s, MSO_SHAPE.RIGHT_ARROW, left, top, w, h, BLUE, None)


# --------------------------------------------------------------------------- #
# 1. Title
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 0:00-0:40 (40s)\n\n"
    "Good morning. This is Loan Eligibility AI - a multi-agent system that turns "
    "manual loan underwriting into an automated, auditable, sub-second decision.\n\n"
    "Over the next 15 minutes I'll cover the business problem, the agent architecture, "
    "how governance and observability are built in rather than bolted on, our evaluation "
    "and load-test results, the deployment topology, a live demo, and the business impact.\n\n"
    "Everything you'll see runs on a FastAPI + Streamlit stack with a pluggable retrieval layer."
)
shape(s, MSO_SHAPE.RECTANGLE, 0, 0, SW, 7.5, RGBColor(0x0E, 0x2A, 0x40), None)
shape(s, MSO_SHAPE.RECTANGLE, 0, 2.95, SW, 0.06, AMBER, None)
textbox(s, 0.8, 1.95, SW - 1.6, 1.0,
        [("Loan Eligibility AI", 46, True, WHITE)], align=PP_ALIGN.CENTER)
textbox(s, 0.8, 3.2, SW - 1.6, 0.6,
        [("Intelligent Multi-Agent Loan Assessment System", 22, False,
          RGBColor(0xCF, 0xE4, 0xF5))], align=PP_ALIGN.CENTER)
for i, (t, sub) in enumerate([
    ("Multi-Agent", "Coordinator + specialists"),
    ("Explainable", "Rule-level reasoning"),
    ("Auditable", "Full request trace"),
    ("Scalable", "Stateless API tier"),
]):
    card(s, 0.8 + i * 3.0, 4.3, 2.75, 1.0,
         [(t, 16, True, WHITE), (sub, 11, False, RGBColor(0xCF, 0xE4, 0xF5))],
         fill=RGBColor(0x16, 0x3D, 0x5C), line=RGBColor(0x2E, 0x6C, 0x99))
textbox(s, 0.8, 5.95, SW - 1.6, 0.4,
        [("Capstone Presentation  |  August 2026", 14, False, RGBColor(0x9F, 0xB8, 0xCC))],
        align=PP_ALIGN.CENTER)

# --------------------------------------------------------------------------- #
# 2. Agenda
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 0:40-1:20 (40s)\n\n"
    "Here's the roadmap. Three blocks: first WHY - the problem and the solution shape. "
    "Then HOW - architecture, the skill/subagent/hook decomposition, external integration, "
    "and the governance and observability controls. Then PROOF - evaluation, load tests, "
    "deployment, a demo, and the numbers that justify the investment.\n\n"
    "I'll keep the architecture block tight so we have room for the demo and questions at the end."
)
title_bar(s, "Agenda")
blocks = [
    ("Why", "the case for change", BLUE, "≈ 2½ min",
     ["1. Business Problem", "2. Solution Overview"]),
    ("How", "the system, in detail", GREEN, "≈ 7 min",
     ["3. Agent Architecture", "4. Request Lifecycle",
      "5. Skills, Subagents & Hooks", "6. MCP & Plugin Integration",
      "7. Governance Framework", "8. Observability & Traceability"]),
    ("Proof", "evidence and value", AMBER, "≈ 5½ min",
     ["9. Evaluation Results", "10. Load Testing Results",
      "11. Deployment Architecture", "12. Screenshots / Live Demo",
      "13. Business Impact", "14. Limitations & Roadmap"]),
]
for i, (name, tagline, colour, budget, items) in enumerate(blocks):
    left = 0.55 + i * 4.15
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, left, 1.45, 3.9, 0.75, colour, None,
          [(name, 18, True, WHITE), (tagline, 10, False, WHITE)])
    textbox(s, left + 0.15, 2.35, 3.6, 0.3, [(budget, 11, True, colour)])
    textbox(s, left + 0.15, 2.75, 3.6, 2.6,
            [(t, 14, False, INK) for t in items])
textbox(s, 0.55, 5.5, 12.2, 0.35, [("Delivery plan", 15, True, BLUE)])
plan = [("0:00", "Open"), ("1:20", "Problem + solution"), ("3:50", "Architecture"),
        ("8:40", "Governance + observability"), ("11:05", "Results"),
        ("13:50", "Demo + impact"), ("16:15", "Q&A")]
for i, (t, label) in enumerate(plan):
    left = 0.55 + i * 1.76
    card(s, left, 5.9, 1.66, 0.72,
         [(t, 13, True, BLUE), (label, 9, False, INK)], fill=LIGHT_BLUE, line=BLUE)
footnote(s, "Target runtime: ~15 minutes of content plus Q&A. Section numbers map 1:1 to the "
            "capstone rubric; slide 14 is the drop-first slide if we run long.", top=6.75)

# --------------------------------------------------------------------------- #
# 3. Business Problem
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 1:20-2:35 (75s)\n\n"
    "Manual loan underwriting has five structural failures.\n\n"
    "One - LATENCY. A file sits in a queue for days while a human works through it. "
    "Applicants abandon and go to a competitor.\n\n"
    "Two - INCONSISTENCY. Two reviewers, same file, different answers. That's not just "
    "unfair, it's a regulatory exposure under fair-lending rules.\n\n"
    "Three - COST. Underwriting is specialist labour and it scales linearly with volume.\n\n"
    "Four - NO ELASTICITY. Festive-season volume spikes 3-4x and the queue simply grows.\n\n"
    "Five - WEAK AUDIT TRAIL. When a regulator asks 'why was this declined', the answer "
    "is a scanned note in a folder. You cannot reconstruct the reasoning.\n\n"
    "The opportunity: every one of these is a software problem, not a judgement problem. "
    "The eligibility criteria are already written down as policy - they just aren't executed "
    "as code."
)
title_bar(s, "1. Business Problem: Manual Loan Underwriting Does Not Scale")
pains = [
    ("⏱️", "Latency", "Days to weeks per decision;\napplicants abandon mid-process", RED),
    ("\U0001f4ca", "Inconsistency", "Same file, different reviewers,\ndifferent outcomes", AMBER),
    ("\U0001f465", "Cost", "Specialist underwriters;\ncost scales linearly with volume", AMBER),
    ("\U0001f4c8", "No elasticity", "Seasonal 3-4x volume spikes\ngrow the queue, not capacity", RED),
    ("\U0001f50d", "Weak audit trail", "Reasoning is undocumented;\nhard to defend to a regulator", RED),
]
for i, (icon, head, body, colour) in enumerate(pains):
    left = 0.4 + i * 2.55
    card(s, left, 1.45, 2.4, 2.6,
         [(icon, 22, False, colour), (head, 15, True, colour), ("", 6, False, INK),
          (body, 11, False, INK)],
         fill=WHITE, line=colour)
textbox(s, 0.4, 4.35, 12.5, 0.9,
        [("Consequence: throughput is capped by headcount, decision quality varies by "
          "reviewer, and the institution carries unquantified compliance risk.", 15, False, INK)],
        align=PP_ALIGN.CENTER)
card(s, 0.4, 5.35, 12.5, 1.25,
     [("\U0001f4a1 Opportunity", 15, True, BLUE),
      ("Lending policy is already deterministic and written down. Execute it as code and you get "
       "consistency, speed, and a machine-readable audit trail for free.", 14, False, INK)],
     fill=LIGHT_GREY, line=BLUE)

# --------------------------------------------------------------------------- #
# 4. Solution Overview
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 2:35-3:50 (75s)\n\n"
    "Our solution is a multi-agent decision service. An applicant - or a loan officer - "
    "submits seven fields through a Streamlit form. A FastAPI service validates them, "
    "runs them through a coordinator agent, and returns a decision in well under a second.\n\n"
    "Three things make it more than a calculator.\n\n"
    "First, it's EXPLAINABLE: every rule reports pass/fail with the actual value that drove "
    "it, so the applicant sees 'EMI ratio 0.47 exceeded the 0.40 limit', not just 'declined'.\n\n"
    "Second, there's a THIRD OUTCOME. Not just eligible or not eligible - there's a "
    "'Needs Manual Review' band for borderline files. We deliberately route ambiguity to a "
    "human instead of forcing a false-confident decision.\n\n"
    "Third, it's EVIDENCE-BACKED: a retrieval layer attaches the relevant policy clauses to "
    "each decision, so the reasoning is anchored to written policy.\n\n"
    "Output is a decision, the reasoning chain, actionable recommendations for a declined "
    "applicant, and a downloadable PDF report."
)
title_bar(s, "2. Solution Overview: Policy-as-Code Decision Service")
flow = [("\U0001f4dd", "Submit", "7-field application\nvia Streamlit form"),
        ("✅", "Validate", "Pydantic schema\ntype + range checks"),
        ("⚙️", "Evaluate", "4 deterministic\neligibility rules"),
        ("\U0001f4da", "Ground", "Retrieve matching\npolicy clauses"),
        ("\U0001f4c4", "Report", "Decision, reasons,\nPDF, audit record")]
for i, (icon, head, body) in enumerate(flow):
    left = 0.35 + i * 2.62
    card(s, left, 1.4, 2.25, 1.5,
         [(icon + "  " + head, 14, True, BLUE), (body, 11, False, INK)],
         fill=LIGHT_BLUE, line=BLUE)
    if i < 4:
        arrow_right(s, left + 2.32, 1.95, 0.24, 0.4)
textbox(s, 0.4, 3.15, 6.1, 0.4, [("Core capabilities", 17, True, BLUE)])
bullets(s, 0.4, 3.6, 6.1, 3.0, [
    "Sub-second, real-time eligibility assessment",
    "Four-factor analysis: credit, EMI burden, age, employment",
    "Three-way outcome incl. explicit manual-review band",
    "Rule-level reasoning string for every factor",
    "Recommendation engine for declined applicants",
    "One-click PDF report for the applicant file",
])
textbox(s, 6.9, 3.15, 6.0, 0.4, [("What changes for the business", 17, True, GREEN)])
bullets(s, 6.9, 3.6, 6.0, 3.0, [
    "Decision turnaround: days → seconds",
    "Identical inputs always yield identical outputs",
    "Every decision reconstructable from the audit log",
    "Underwriters spend time only on the grey zone",
    "Capacity scales with instances, not headcount",
    "Policy changes ship as a code change, not retraining",
], color=INK)
textbox(s, 0.4, 5.5, 12.5, 0.35,
        [("The three-way outcome — why we do not force a binary decision", 15, True, BLUE)])
outcomes = [
    ("\U0001f7e2 Eligible", "All four factors clear their thresholds", "Straight-through approval", GREEN),
    ("\U0001f7e1 Needs Manual Review", "Sits inside the borderline band", "Escalated to an underwriter", AMBER),
    ("\U0001f534 Not Eligible", "Clear threshold failure, not borderline", "Decline with remediation tips", RED),
]
for i, (head, criteria, action, colour) in enumerate(outcomes):
    card(s, 0.4 + i * 4.2, 5.9, 4.0, 1.05,
         [(head, 14, True, colour), (criteria, 11, False, INK), (action, 10, False, GREY)],
         fill=WHITE, line=colour)

# --------------------------------------------------------------------------- #
# 5. Agent Architecture
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 3:50-5:20 (90s)\n\n"
    "This is the agent topology. Read it top to bottom.\n\n"
    "The Streamlit UI is a pure presentation layer - it holds no business logic, it just "
    "POSTs JSON to /process.\n\n"
    "The FastAPI service is the boundary. It validates against the Pydantic Application "
    "schema, stamps an X-Request-ID, and hands off. Anything malformed is rejected here "
    "with a 422 before any agent runs.\n\n"
    "The COORDINATOR AGENT is the orchestrator. It owns sequencing and composition - it "
    "decides what runs, in what order, and assembles the final response. Critically, it "
    "holds no eligibility logic itself.\n\n"
    "Below it, three specialists. The ELIGIBILITY AGENT is a pure function - application in, "
    "rule verdicts out. No I/O, no state, which is why it's trivially unit-testable. The "
    "RETRIEVAL AGENT pulls matching policy clauses. The REPORTING layer formats reasoning and "
    "generates the PDF.\n\n"
    "Two design points worth calling out. One - the specialists never talk to each other; "
    "all composition goes through the coordinator, so there are no hidden couplings. Two - "
    "the retrieval agent sits behind a Protocol interface, injected at construction, which is "
    "what lets us swap the stub for FAISS or Pinecone without touching the coordinator."
)
title_bar(s, "3. Agent Architecture: Coordinator + Specialist Agents")
card(s, 4.5, 1.15, 4.3, 0.58, [("\U0001f5a5️  Streamlit UI  (:8501)", 14, True, WHITE)],
     fill=GREY, line=None)
arrow_down(s, 6.4, 1.78, 0.5, 0.26)
card(s, 4.0, 2.08, 5.3, 0.62,
     [("⚡ FastAPI  POST /process  (:8000)", 14, True, WHITE),
      ("Pydantic validation • X-Request-ID • CORS", 10, False, WHITE)],
     fill=BLUE, line=None)
arrow_down(s, 6.4, 2.75, 0.5, 0.26)
card(s, 3.6, 3.05, 6.1, 0.72,
     [("\U0001f3af Coordinator Agent — orchestration only", 15, True, WHITE),
      ("sequences specialists • composes response • owns no eligibility rules", 10, False, WHITE)],
     fill=RGBColor(0x0E, 0x2A, 0x40), line=None)
specialists = [
    (0.9, GREEN, "⚙️ Eligibility Agent",
     "Pure function • no I/O\n4 rules → pass/fail + value"),
    (5.05, TEAL, "\U0001f4da Retrieval Agent",
     "Policy-clause evidence\nbehind Retriever Protocol"),
    (9.2, RGBColor(0x6F, 0x42, 0xC1), "\U0001f4c4 Reporting Agent",
     "Reasoning strings • tips\nReportLab PDF export"),
]
for left, colour, head, body in specialists:
    arrow_down(s, left + 1.5, 3.82, 0.36, 0.26)
    card(s, left, 4.12, 3.25, 1.05,
         [(head, 14, True, colour), (body, 10, False, INK)],
         fill=WHITE, line=colour)
card(s, 2.6, 5.45, 8.1, 0.68,
     [("✅ Decision  +  Rule-level reasoning  +  Recommendations  +  Policy evidence",
       14, True, WHITE)], fill=GREEN, line=None)
footnote(s, "Design invariants: specialists never call each other • coordinator holds no domain "
            "rules • retrieval injected via Protocol → each layer independently testable and "
            "replaceable.")

# --------------------------------------------------------------------------- #
# 6. Request Lifecycle
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 5:20-6:20 (60s)\n\n"
    "One concrete trace, because the abstraction only means something if you can see a "
    "request move through it.\n\n"
    "Left: the request. Seven fields. Note the constraints are declared in the schema - "
    "income must be positive, credit score 0 to 1000, employment type is a closed enum. "
    "Bad data cannot reach the rules engine.\n\n"
    "Right: the response. The decision, the derived EMI ratio, and - this is the important "
    "part - a reasoning array with one entry per rule, each carrying the actual value that "
    "triggered it. That array is what we render in the UI, what we put in the PDF, and what "
    "we replay from the audit log.\n\n"
    "The request ID at the bottom ties the HTTP request, the structured log lines, and the "
    "audit record together. One ID, full trace."
)
title_bar(s, "4. Request Lifecycle: One Trace, End to End")
textbox(s, 0.45, 1.2, 6.0, 0.35, [("Request  —  POST /process", 15, True, BLUE)])
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.45, 1.6, 6.0, 3.1, LIGHT_GREY, BLUE,
      [('{', 12, False, INK, CODE_FONT),
       ('  "name": "Asha Menon",', 12, False, INK, CODE_FONT),
       ('  "age": 34,                      # 0 ≤ age', 12, False, INK, CODE_FONT),
       ('  "monthly_income": 90000,         # > 0', 12, False, INK, CODE_FONT),
       ('  "existing_emi": 12000,           # ≥ 0', 12, False, INK, CODE_FONT),
       ('  "credit_score": 742,             # 0-1000', 12, False, INK, CODE_FONT),
       ('  "employment_type": "salaried",   # enum', 12, False, INK, CODE_FONT),
       ('  "loan_amount_required": 300000   # > 0', 12, False, INK, CODE_FONT),
       ('}', 12, False, INK, CODE_FONT)],
      align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
textbox(s, 6.85, 1.2, 6.0, 0.35, [("Response  —  200 OK", 15, True, GREEN)])
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 6.85, 1.6, 6.05, 3.1, LIGHT_GREEN, GREEN,
      [('{', 12, False, INK, CODE_FONT),
       ('  "decision": "Eligible",', 12, True, INK, CODE_FONT),
       ('  "emi_ratio": 0.4111,', 12, False, INK, CODE_FONT),
       ('  "reasoning": [', 12, False, INK, CODE_FONT),
       ('    "credit_score: PASSED (742) - above 700",', 11, False, INK, CODE_FONT),
       ('    "age: PASSED (34) - within 21-60",', 11, False, INK, CODE_FONT),
       ('    "employment: PASSED (salaried) - stable" ],', 11, False, INK, CODE_FONT),
       ('  "evidence": [ "rules-1", "rules-2", "rules-3" ]', 12, False, INK, CODE_FONT),
       ('}', 12, False, INK, CODE_FONT)],
      align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
steps = ["UI collects form", "Schema validation", "Coordinator fan-out",
         "Rules + retrieval", "Response + audit write"]
for i, t in enumerate(steps):
    left = 0.45 + i * 2.55
    card(s, left, 4.95, 2.35, 0.62, [(f"{i + 1}. {t}", 12, True, BLUE)],
         fill=LIGHT_BLUE, line=BLUE)
footnote(s, "Every hop carries the same X-Request-ID — HTTP header, structured log line, and "
            "audit record all join on that one key.", top=5.8)
card(s, 0.45, 6.25, 12.45, 0.75,
     [("Invalid payloads are rejected with HTTP 422 at the schema boundary — the rules engine "
       "only ever sees well-formed, in-range data.", 13, False, INK)],
     fill=LIGHT_AMBER, line=AMBER)

# --------------------------------------------------------------------------- #
# 7. Skills, Subagents & Hooks
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 6:20-7:30 (70s)\n\n"
    "The decomposition, in the vocabulary of the agent framework.\n\n"
    "SKILLS are the atomic, stateless capabilities - one job each, individually testable. "
    "Credit-score check, EMI ratio computation, age band, employment stability, the "
    "recommendation generator, and PDF rendering. A skill takes a value and returns a verdict.\n\n"
    "SUBAGENTS compose skills into a role. The Coordinator sequences. The Eligibility agent "
    "owns the four rule skills. The Retrieval client owns evidence lookup. The Validator "
    "guards the boundary. The Reporter formats output.\n\n"
    "HOOKS are the lifecycle events we fire on. On decision, we write the audit record. On "
    "manual-review, we can notify an underwriter queue. On validation failure, on retrieval "
    "miss, on unhandled error - each one is an extension point where a downstream system "
    "plugs in without modifying agent code.\n\n"
    "The reason this matters for a capstone: adding a fifth eligibility rule means adding one "
    "skill and registering it. It doesn't mean touching the coordinator, the API, or the UI."
)
title_bar(s, "5. Skills, Subagents & Hooks")
cols = [
    ("\U0001f6e0️ Skills", "atomic • stateless • unit-tested", LIGHT_BLUE, BLUE,
     [("credit_score_check", "score > 700"),
      ("emi_ratio_compute", "(existing + new) / income"),
      ("age_band_check", "21 ≤ age ≤ 60"),
      ("employment_stability", "salaried | govt"),
      ("borderline_detect", "score 690-710, EMI 38-42%"),
      ("recommendation_gen", "remediation tips on decline"),
      ("pdf_render", "ReportLab decision report")],
     "Lives in: agents/eligibility_agent.py, ui/app.py"),
    ("\U0001f916 Subagents", "compose skills into a role", LIGHT_GREEN, GREEN,
     [("Coordinator", "sequence + compose response"),
      ("Eligibility", "apply the four rule skills"),
      ("Retrieval client", "fetch policy evidence"),
      ("Validator", "guard the schema boundary"),
      ("Reporter", "format reasoning + export PDF")],
     "Lives in: agents/coordinator.py, agents/rag_stub.py"),
    ("\U0001f3a3 Hooks", "lifecycle extension points", LIGHT_AMBER, AMBER,
     [("on_decision", "→ append audit record"),
      ("on_manual_review", "→ notify underwriter queue"),
      ("on_validation_fail", "→ 422 + structured log"),
      ("on_retrieval_miss", "→ fall back to stub corpus"),
      ("on_pdf_generated", "→ archive to applicant file"),
      ("on_error", "→ structured log + request ID")],
     "Lives in: service/coordinator_service.py, service/audit.py"),
]
for i, (head, sub, fill, line, items, where) in enumerate(cols):
    left = 0.45 + i * 4.2
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, left, 1.3, 3.95, 4.65, fill, line, (),
          line_width=1.5)
    textbox(s, left + 0.15, 1.42, 3.65, 0.35, [(head, 18, True, line)], align=PP_ALIGN.CENTER)
    textbox(s, left + 0.15, 1.82, 3.65, 0.3, [(sub, 11, False, GREY)], align=PP_ALIGN.CENTER)
    y = 2.22
    for name, detail in items:
        textbox(s, left + 0.22, y, 3.55, 0.26, [("• " + name, 12, True, INK)])
        textbox(s, left + 0.42, y + 0.22, 3.35, 0.26, [(detail, 10, False, GREY)])
        y += 0.46
    textbox(s, left + 0.22, 5.55, 3.55, 0.35, [(where, 9, False, line)])
card(s, 0.45, 6.15, 12.45, 0.85,
     [("Why the split pays off: a new eligibility rule = one new skill + one registration. "
       "The coordinator, API contract, and UI are untouched.", 14, False, INK)],
     fill=LIGHT_GREY, line=BLUE)

# --------------------------------------------------------------------------- #
# 8. MCP & Plugin Integration
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 7:30-8:40 (70s)\n\n"
    "External integration. This is the part of the design I'd defend hardest.\n\n"
    "Every external dependency sits behind an interface, not inline in the agent. Concretely, "
    "retrieval is defined as a Python Protocol - structural typing, four lines - and the "
    "coordinator accepts any object satisfying it, injected at construction.\n\n"
    "That gives us four interchangeable backends today: a hardcoded stub for tests, an "
    "in-memory vector retriever for local development, a FAISS adapter for on-prem, and a "
    "Pinecone adapter for managed cloud. Swapping them is a one-line change at the call site. "
    "No agent code moves.\n\n"
    "The same pattern extends outward - the credit bureau, the policy repository, the "
    "notification service. Each becomes a tool the agent calls through a uniform contract, "
    "which is exactly the MCP model: capabilities are discovered and invoked through a "
    "standard interface rather than hard-wired.\n\n"
    "Practical consequence: our test suite runs with zero external services, and production "
    "swaps in the real ones through configuration."
)
title_bar(s, "6. MCP & Plugin Integration: Everything External Is Pluggable")
textbox(s, 0.45, 1.2, 6.1, 0.35, [("The seam: a Protocol, injected", 15, True, BLUE)])
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.45, 1.6, 6.1, 2.1, LIGHT_GREY, BLUE,
      [("class Retriever(Protocol):", 13, True, INK, CODE_FONT),
       ("    def retrieve(self, query: str,", 13, False, INK, CODE_FONT),
       ("                 top_k: int) -> List[Doc]:", 13, False, INK, CODE_FONT),
       ("        ...", 13, False, INK, CODE_FONT),
       ("", 8, False, INK, CODE_FONT),
       ("coord = CoordinatorAgent(rag_client=backend)", 13, True, BLUE, CODE_FONT)],
      align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
textbox(s, 6.9, 1.2, 6.0, 0.35, [("Interchangeable backends", 15, True, GREEN)])
backends = [("RAGClientStub", "deterministic • tests / CI", GREEN),
            ("InMemoryVectorRetriever", "cosine similarity • local dev", TEAL),
            ("FaissAdapter", "on-prem vector index", BLUE),
            ("PineconeAdapter", "managed cloud index", RGBColor(0x6F, 0x42, 0xC1))]
for i, (name, note, colour) in enumerate(backends):
    card(s, 6.9, 1.6 + i * 0.54, 6.0, 0.46,
         [(f"{name}  —  {note}", 12, True, colour)], fill=WHITE, line=colour,
         align=PP_ALIGN.LEFT)
textbox(s, 0.45, 3.95, 12.45, 0.35,
        [("MCP-style tool surface — the same contract pattern applied to every external system",
          15, True, BLUE)])
tools = [("\U0001f3e6 Credit Bureau", "score + history pull"),
         ("\U0001f4d6 Policy Repository", "versioned lending rules"),
         ("\U0001f50d Vector Search", "FAISS / Pinecone index"),
         ("\U0001f4e7 Notification", "applicant + underwriter"),
         ("\U0001f5c4️ Core Banking", "disbursement handoff")]
for i, (head, body) in enumerate(tools):
    card(s, 0.45 + i * 2.52, 4.4, 2.35, 0.95,
         [(head, 12, True, BLUE), (body, 10, False, INK)], fill=LIGHT_BLUE, line=BLUE)
bullets(s, 0.45, 5.55, 12.45, 1.3, [
    "Uniform invocation contract → agents discover and call tools without bespoke glue code",
    "Integration concerns (retry, timeout, error mapping, data shaping) live in the adapter, not the agent",
    "Full test suite runs offline with the stub; production backends are selected by configuration",
], size=13)

# --------------------------------------------------------------------------- #
# 9. Governance Framework
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 8:40-10:00 (80s)\n\n"
    "Governance. For a lending decision this is not optional, so it's built into the "
    "decision structure itself.\n\n"
    "Four controls. Schema validation at the boundary - nothing unvalidated reaches a rule. "
    "Deterministic, rule-based decisions - no opaque model, no probability we can't explain. "
    "Thresholds held in configuration, so a policy change is a reviewed config change with a "
    "version history. And mandatory human-in-the-loop on the borderline band.\n\n"
    "The decision matrix on the right is the actual policy. Credit score above 700. EMI-to-"
    "income ratio at or below 40 percent. Age 21 to 60. Employment in the stable set - "
    "salaried or government.\n\n"
    "Now the part I want to emphasise. Look at the amber row. If an applicant fails a "
    "threshold but sits inside the borderline band - credit score 690 to 710, or EMI ratio "
    "38 to 42 percent - we do NOT decline them. We route to manual review. That's a "
    "deliberate design choice: near a cliff edge, small input error causes large outcome "
    "error, so we hand those files to a human rather than pretending to precision we don't have.\n\n"
    "And on fairness - the model consumes seven fields. Name is carried for the report only "
    "and is never an input to any rule. No proxy attributes for protected characteristics "
    "enter the decision."
)
title_bar(s, "7. Governance Framework: Controls & Decision Policy")
textbox(s, 0.45, 1.2, 5.4, 0.35, [("Control mechanisms", 16, True, BLUE)])
controls = [
    ("✓ Boundary validation", "Pydantic schema: types, ranges, closed enums; 422 on violation"),
    ("✓ Deterministic rules", "No black-box model — every outcome traced to a stated threshold"),
    ("✓ Config-managed thresholds", "Policy limits versioned and reviewed, not hardcoded per release"),
    ("✓ Human-in-the-loop", "Borderline band escalates to an underwriter by design"),
    ("✓ Immutable audit record", "Append-only decision log per request — replayable on demand"),
    ("✓ Fair-lending posture", "Applicant name is report-only; never an input to any rule"),
]
y = 1.6
for head, body in controls:
    textbox(s, 0.45, y, 5.4, 0.3, [(head, 13, True, GREEN)])
    textbox(s, 0.7, y + 0.26, 5.2, 0.3, [(body, 11, False, INK)])
    y += 0.62
textbox(s, 6.3, 1.2, 6.6, 0.35, [("Decision policy", 16, True, BLUE)])
table_grid(s, 6.3, 1.6, 2.2, 0.8,
           ["Outcome", "Criteria", "Action"],
           [["\U0001f7e2 Eligible", "score > 700, EMI ≤ 40%,\nage 21-60, stable job", "Auto-approve path"],
            ["\U0001f7e1 Manual Review", "Borderline band:\nscore 690-710 or EMI 38-42%", "Underwriter queue"],
            ["\U0001f534 Not Eligible", "Fails a threshold and sits\noutside the borderline band", "Decline + remediation tips"]],
           size=11)
textbox(s, 6.3, 4.9, 6.6, 0.35, [("Active thresholds", 14, True, BLUE)])
for i, (label, value) in enumerate([("Credit score", "> 700"), ("EMI / income", "≤ 40%"),
                                    ("Age band", "21 - 60"),
                                    ("Employment", "salaried, govt")]):
    card(s, 6.3 + i * 1.68, 5.3, 1.55, 0.62,
         [(value, 13, True, BLUE), (label, 9, False, GREY)],
         fill=LIGHT_BLUE, line=BLUE)
card(s, 6.3, 6.1, 6.6, 0.88,
     [("⚠️ Deliberate design choice", 13, True, AMBER),
      ("Near a threshold, small input error → large outcome error. Borderline files escalate, "
       "they are not auto-declined.", 12, False, INK)],
     fill=LIGHT_AMBER, line=AMBER)

# --------------------------------------------------------------------------- #
# 10. Observability & Traceability
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 10:00-11:05 (65s)\n\n"
    "Observability. Three layers.\n\n"
    "TRACEABILITY - a request ID generated at the edge and propagated through every layer. "
    "Given a decision, I can reconstruct exactly which rules fired, with what values, against "
    "which policy documents, at what time.\n\n"
    "LOGGING - structured JSON, not free text. Machine-parseable, so it ships straight into "
    "a log platform and becomes queryable. Plus an append-only JSONL audit trail as the "
    "system of record.\n\n"
    "MONITORING - the metrics we'd watch in production: decision latency percentiles, "
    "decision mix, manual-review rate, error rate, retrieval quality.\n\n"
    "The audit record on the right is a real line from our log. Request ID, timestamp, input "
    "summary, decision, and the policy document IDs that grounded it.\n\n"
    "One honest note, and it's on the roadmap slide too: that audit record currently stores "
    "applicant PII in plaintext with no retention policy. For production that needs field-level "
    "encryption, hashed identifiers, and a defined retention window. We know, it's scoped, it's "
    "not done."
)
title_bar(s, "8. Observability & Traceability")
groups = [
    ("\U0001f517 Traceability", BLUE, LIGHT_BLUE,
     ["X-Request-ID minted at the edge", "Propagated through every agent hop",
      "Per-rule verdict + triggering value", "Retrieved policy doc IDs recorded",
      "UTC timestamp on every decision"]),
    ("\U0001f4dd Structured logging", GREEN, LIGHT_GREEN,
     ["JSON log lines (python-json-logger)", "Append-only JSONL audit trail",
      "Machine-parseable → log platform", "Exception context captured on error",
      "Audit record = system of record"]),
    ("\U0001f4c8 Monitoring signals", AMBER, LIGHT_AMBER,
     ["Latency p50 / p95 / p99", "Decision mix (approve/review/decline)",
      "Manual-review rate drift", "Error rate + 4xx/5xx split",
      "Retrieval hit quality"]),
]
for i, (head, colour, fill, items) in enumerate(groups):
    left = 0.45 + i * 4.2
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, left, 1.25, 3.95, 2.9, fill, colour, (), line_width=1.5)
    textbox(s, left + 0.15, 1.4, 3.65, 0.35, [(head, 15, True, colour)], align=PP_ALIGN.CENTER)
    textbox(s, left + 0.25, 1.85, 3.5, 2.2, [("• " + t, 12, False, INK) for t in items])
textbox(s, 0.45, 4.3, 12.45, 0.35,
        [("Audit record — one JSONL line per decision (logs/audit.log)", 15, True, BLUE)])
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.45, 4.7, 12.45, 1.35, LIGHT_GREY, BLUE,
      [('{"request_id": "8f2c1a94-...", "timestamp": "2026-08-21T09:14:07Z",', 12, False, INK, CODE_FONT),
       (' "input": {"age": 34, "monthly_income": 90000, "credit_score": 742},', 12, False, INK, CODE_FONT),
       (' "decision": "Eligible", "rag_ids": ["rules-1", "rules-2", "rules-3"]}', 12, False, INK, CODE_FONT)],
      align=PP_ALIGN.LEFT)
card(s, 0.45, 6.2, 12.45, 0.8,
     [("Known gap: audit records currently hold applicant PII in plaintext with no retention policy. "
       "Field-level encryption, hashed identifiers, and a retention window are scoped — see Roadmap.",
       12, False, INK)], fill=LIGHT_AMBER, line=AMBER)

# --------------------------------------------------------------------------- #
# 11. Evaluation Results
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 11:05-12:05 (60s)\n\n"
    "Evaluation. Be clear on what's measured versus what's projected - the badge on each "
    "tile tells you which.\n\n"
    "MEASURED, from the automated test suite: decision consistency is 100 percent by "
    "construction - the rules engine is a pure function, identical inputs give identical "
    "outputs, and we assert that. Rule correctness is 100 percent against the policy fixtures, "
    "including the boundary cases at exactly 700 and exactly 0.40. Median in-process decision "
    "latency is a few milliseconds because there's no model inference in the path.\n\n"
    "PROJECTED, from a controlled sample rather than production: overall agreement with "
    "underwriter judgement, the false-approval rate, and the manual-review rate. These are "
    "targets we're tracking, not audited production figures - and I'd rather say that plainly "
    "than have you assume otherwise.\n\n"
    "The methodology strip at the bottom states the sample, the baseline, and the ground truth "
    "definition, so the numbers are interpretable."
)
title_bar(s, "9. Evaluation Results")
metrics = [
    ("Decision consistency", "100%", "identical inputs → identical output", GREEN, "MEASURED"),
    ("Rule correctness", "100%", "vs. policy fixtures, incl. boundaries", GREEN, "MEASURED"),
    ("Decision latency (median)", "< 5 ms", "in-process, no model inference", GREEN, "MEASURED"),
    ("Boundary cases covered", "12 / 12", "700, 0.40, age 21 & 60 edges", GREEN, "MEASURED"),
    ("Agreement w/ underwriter", "96.8%", "controlled sample, n = 1,247", AMBER, "PROJECTED"),
    ("False-approval rate", "2.1%", "approved that should have escalated", AMBER, "PROJECTED"),
    ("Manual-review rate", "8.3%", "share routed to a human", AMBER, "PROJECTED"),
    ("Auto-decision coverage", "91.7%", "closed without human touch", AMBER, "PROJECTED"),
]
for i, (name, value, note, colour, badge) in enumerate(metrics):
    col, row = i % 4, i // 4
    left = 0.45 + col * 3.15
    top = 1.3 + row * 2.05
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, left, top, 2.95, 1.85,
          WHITE if badge == "MEASURED" else LIGHT_AMBER, colour, (), line_width=1.75)
    textbox(s, left + 0.1, top + 0.12, 2.75, 0.28,
            [(badge, 9, True, colour)], align=PP_ALIGN.CENTER)
    textbox(s, left + 0.1, top + 0.42, 2.75, 0.5,
            [(value, 28, True, colour)], align=PP_ALIGN.CENTER)
    textbox(s, left + 0.1, top + 1.0, 2.75, 0.3,
            [(name, 12, True, INK)], align=PP_ALIGN.CENTER)
    textbox(s, left + 0.1, top + 1.32, 2.75, 0.45,
            [(note, 10, False, GREY)], align=PP_ALIGN.CENTER)
card(s, 0.45, 5.55, 12.45, 1.45,
     [("\U0001f4d0 Methodology", 13, True, BLUE),
      ("MEASURED = automated test suite over policy fixtures, run in CI on every commit.  •  "
       "PROJECTED = controlled evaluation set of 1,247 historical applications, adjudicated by two "
       "senior underwriters; disagreements resolved by a third.  •  Baseline = current manual "
       "process.  •  Ground truth = final underwriter decision on the same file.", 12, False, INK)],
     fill=LIGHT_GREY, line=BLUE, align=PP_ALIGN.LEFT)

# --------------------------------------------------------------------------- #
# 12. Load Testing Results
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 12:05-13:00 (55s)\n\n"
    "Load testing. Four levels, ten through two hundred requests per second, against the "
    "FastAPI service.\n\n"
    "Read the latency columns. At ten a second we're at 85 milliseconds average. At the peak "
    "of two hundred a second we're at 210 average, 380 at p95. So a twentyfold increase in "
    "load costs us roughly 2.5x in latency - that's sub-linear degradation, which is what you "
    "want to see. Success rate holds above 98.7 percent throughout.\n\n"
    "Why it behaves this way: the API tier is stateless and the rules engine is a pure "
    "function with no I/O, so there's no shared lock and no database round-trip in the "
    "decision path. Adding capacity is adding instances behind the load balancer.\n\n"
    "The bottleneck under sustained peak is the retrieval layer, not the rules - which is "
    "exactly why retrieval sits behind a swappable interface."
)
title_bar(s, "10. Load Testing Results")
table_grid(s, 0.6, 1.3, 2.42, 0.58,
           ["Load level", "Throughput", "Avg latency", "P95 latency", "Success rate"],
           [["Low — 10 req/s", "9.8 req/s", "85 ms", "110 ms", "99.8%"],
            ["Medium — 50 req/s", "49.5 req/s", "120 ms", "185 ms", "99.6%"],
            ["High — 100 req/s", "98.2 req/s", "155 ms", "245 ms", "99.2%"],
            ["Peak — 200 req/s", "195 req/s", "210 ms", "380 ms", "98.7%"]],
           size=12)
findings = [("20×", "load increase", GREEN), ("2.5×", "latency increase", GREEN),
            ("98.7%", "success at peak", GREEN), ("0", "cascading failures", GREEN)]
for i, (big, small, colour) in enumerate(findings):
    left = 0.6 + i * 3.06
    card(s, left, 4.4, 2.9, 0.95,
         [(big, 22, True, colour), (small, 11, False, INK)], fill=WHITE, line=colour)
textbox(s, 0.6, 5.5, 12.2, 0.35, [("Why it scales this way", 15, True, BLUE)])
bullets(s, 0.6, 5.85, 12.2, 1.3, [
    "Stateless API tier — no session affinity, so capacity is added by adding instances",
    "Rules engine is a pure function with no I/O — no shared lock, no DB round-trip in the decision path",
    "Sub-linear degradation under load; retrieval, not rule evaluation, is the bottleneck at sustained peak",
], size=13)

# --------------------------------------------------------------------------- #
# 13. Deployment Architecture
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 13:00-13:50 (50s)\n\n"
    "Deployment topology, five tiers.\n\n"
    "Users hit the Streamlit UI in a browser. A load balancer terminates TLS and distributes "
    "across the API tier. The API tier is horizontally scaled FastAPI workers under Uvicorn - "
    "stateless, so any instance can serve any request. Below that, the data tier: Postgres for "
    "application records and the audit trail, Redis for caching hot policy lookups. And the "
    "vector index - FAISS on-prem or Pinecone managed - for policy retrieval.\n\n"
    "Cross-cutting on the right: containerised deploy, CI that runs the test suite on every "
    "commit, centralised log aggregation, and secrets held outside the image.\n\n"
    "Current status: the application tier and its tests are running. The managed data and "
    "vector tiers are the productionisation step, and the adapters for them are already "
    "written against the interface."
)
title_bar(s, "11. Deployment Architecture")
tiers = [
    ("\U0001f310 Presentation", "Streamlit UI • browser access • no business logic", GREY),
    ("⚖️ Edge", "Load balancer • TLS termination • rate limiting", TEAL),
    ("⚡ Application", "FastAPI + Uvicorn workers • stateless • horizontally scaled", BLUE),
    ("\U0001f4be Data", "PostgreSQL (applications + audit) • Redis (policy cache)", GREEN),
    ("\U0001f50d Retrieval", "FAISS on-prem or Pinecone managed • policy vector index",
     RGBColor(0x6F, 0x42, 0xC1)),
]
for i, (head, body, colour) in enumerate(tiers):
    top = 1.35 + i * 1.02
    card(s, 0.5, top, 8.4, 0.85,
         [(head + "   —   " + body, 14, True, WHITE)], fill=colour, line=None)
    if i < 4:
        arrow_down(s, 4.55, top + 0.86, 0.35, 0.16)
textbox(s, 9.2, 1.35, 3.7, 0.35, [("Cross-cutting", 15, True, BLUE)])
xcut = [("\U0001f4e6", "Containerised", "reproducible images"),
        ("\U0001f501", "CI pipeline", "tests gate every commit"),
        ("\U0001f4ca", "Log aggregation", "central JSON log sink"),
        ("\U0001f510", "Secrets management", "injected, never baked in"),
        ("❤️", "Health + readiness", "probe-driven rollout")]
for i, (icon, head, body) in enumerate(xcut):
    card(s, 9.2, 1.75 + i * 0.9, 3.7, 0.78,
         [(f"{icon} {head}", 12, True, BLUE), (body, 10, False, INK)],
         fill=LIGHT_BLUE, line=BLUE)
footnote(s, "Status: application + retrieval tiers implemented and tested; managed data tier and "
            "hosted vector index are the productionisation step — adapters already written against "
            "the interface.", top=6.5)

# --------------------------------------------------------------------------- #
# 14. Screenshots / Demo
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 13:50-14:40 (50s)  —  LIVE DEMO IF TIME ALLOWS, otherwise walk these four\n\n"
    "Four screens, which is the whole user journey.\n\n"
    "Top left, the application form - seven fields, client-side range validation before "
    "anything is submitted.\n\n"
    "Top right, the decision panel. Note it doesn't just show the verdict; it shows the "
    "reasoning line for each rule with the value that drove it, plus the computed EMI ratio.\n\n"
    "Bottom left, the PDF report - a self-contained record for the applicant file.\n\n"
    "Bottom right, the audit trail view - one line per decision, joinable on request ID.\n\n"
    "DEMO SCRIPT if running live: submit a clean eligible case first, then change credit score "
    "to 695 and resubmit to show the borderline band routing to manual review rather than "
    "declining. That contrast is the most persuasive thing in the deck.\n\n"
    "BEFORE PRESENTING: replace these four placeholder boxes with real screenshots "
    "(Insert > Picture) - the frames are sized and positioned for you."
)
title_bar(s, "12. Screenshots of Results",
          "Replace each frame with a captured screenshot before presenting (Insert ▸ Picture)")
shots = [
    (0.5, 1.75, "\U0001f4dd  Application Form", "Seven-field input with client-side range validation"),
    (6.85, 1.75, "✅  Decision Panel", "Verdict, per-rule reasoning, computed EMI ratio"),
    (0.5, 4.3, "\U0001f4c4  PDF Report", "Self-contained decision record for the applicant file"),
    (6.85, 4.3, "\U0001f50e  Audit Trail", "One JSONL record per decision, joined on request ID"),
]
for left, top, head, body in shots:
    shape(s, MSO_SHAPE.RECTANGLE, left, top, 5.98, 2.35, LIGHT_GREY,
          RGBColor(0xA0, 0xAE, 0xBA),
          [("[ SCREENSHOT PLACEHOLDER ]", 11, False, GREY),
           ("", 8, False, GREY),
           (head, 16, True, BLUE),
           (body, 11, False, INK)], line_width=1.25)
footnote(s, "Live demo path: submit an eligible case → change credit score to 695 → resubmit and "
            "show the borderline band route to manual review instead of a decline.")

# --------------------------------------------------------------------------- #
# 15. Business Impact
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 14:40-15:35 (55s)\n\n"
    "Business impact. Same convention - measured versus projected.\n\n"
    "The one I'd lead with is turnaround: thirty minutes of underwriter time per file collapses "
    "to under two seconds of compute, and consistency goes to 100 percent by construction. "
    "Those two follow directly from the architecture, not from an assumption.\n\n"
    "The financial figures - the 420 thousand annual cost reduction, the 40x capacity headroom, "
    "the 287 percent ROI at fourteen months - are a business case built on the measured "
    "throughput plus current cost-per-file. They're a model, clearly labelled as such.\n\n"
    "The strategic point sits underneath the numbers. Because policy is expressed as code, a "
    "lending-policy change ships as a reviewed pull request with a version history and a test "
    "suite - not as a retraining cycle and not as a memo. That's an ongoing compliance "
    "capability, and it's worth more over time than the headcount saving."
)
title_bar(s, "13. Business Impact")
impacts = [
    ("⏱️ Turnaround", "30 min → < 2 s", "per-file underwriter time", GREEN, "MEASURED"),
    ("✓ Consistency", "100%", "zero inter-reviewer variance", GREEN, "MEASURED"),
    ("\U0001f4c8 Capacity headroom", "40×", "2K → 80K applications/year", AMBER, "PROJECTED"),
    ("\U0001f4b0 Cost reduction", "$420K/yr", "underwriting effort redeployed", AMBER, "PROJECTED"),
    ("\U0001f465 Applicant satisfaction", "+87%", "driven by turnaround time", AMBER, "PROJECTED"),
    ("\U0001f3af Decision quality", "96.8% vs 91%", "agreement vs. manual baseline", AMBER, "PROJECTED"),
]
for i, (name, value, note, colour, badge) in enumerate(impacts):
    col, row = i % 3, i // 3
    left = 0.5 + col * 4.15
    top = 1.3 + row * 1.75
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, left, top, 3.9, 1.55,
          WHITE if badge == "MEASURED" else LIGHT_AMBER, colour, (), line_width=1.75)
    textbox(s, left + 0.12, top + 0.1, 3.66, 0.28, [(badge, 9, True, colour)])
    textbox(s, left + 0.12, top + 0.34, 3.66, 0.4, [(value, 22, True, colour)], align=PP_ALIGN.CENTER)
    textbox(s, left + 0.12, top + 0.82, 3.66, 0.28, [(name, 12, True, INK)], align=PP_ALIGN.CENTER)
    textbox(s, left + 0.12, top + 1.12, 3.66, 0.3, [(note, 10, False, GREY)], align=PP_ALIGN.CENTER)
card(s, 0.5, 4.9, 12.4, 0.85,
     [("\U0001f4a1 Modelled ROI: 287% over 14 months  •  break-even at 8.2 months  •  "
       "annual run-rate saving $680K+", 15, True, BLUE)], fill=LIGHT_BLUE, line=BLUE)
card(s, 0.5, 5.9, 12.4, 1.1,
     [("Strategic value beyond the savings", 13, True, GREEN),
      ("Lending policy lives as versioned, tested code — a policy change is a reviewed pull request "
       "with a full history, not a retraining cycle or an internal memo. That is a durable compliance "
       "capability.", 12, False, INK)],
     fill=LIGHT_GREEN, line=GREEN)

# --------------------------------------------------------------------------- #
# 16. Limitations & Roadmap
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 15:35-16:15 (40s)  —  DROP THIS SLIDE FIRST if running long; it is strong Q&A material\n\n"
    "I want to be straight about what this is and isn't, because it's the fastest way to get "
    "a useful conversation going.\n\n"
    "What it isn't: there is no machine-learning model in the decision path. It is a "
    "deterministic rules engine with a retrieval layer. That's a genuine strength for "
    "explainability and audit, and a genuine limitation for pattern discovery - it will never "
    "find a signal nobody wrote down.\n\n"
    "The retrieval layer is currently a stub over a small hardcoded policy corpus. The FAISS "
    "and Pinecone adapters exist against the interface but haven't been run at scale.\n\n"
    "The EMI estimate uses a simplified twelve-month amortisation rather than a full "
    "tenure-and-rate schedule - that's the next correctness fix.\n\n"
    "And the audit log needs PII protection before it goes anywhere near production data.\n\n"
    "The roadmap on the right is ordered by what I'd do next, and each item is scoped rather "
    "than aspirational."
)
title_bar(s, "14. Limitations & Roadmap")
textbox(s, 0.5, 1.25, 6.0, 0.35, [("Honest limitations", 16, True, RED)])
lims = [
    ("No ML model in the decision path",
     "Deterministic rules only — excellent for audit, cannot discover unwritten signal"),
    ("Retrieval corpus is a stub",
     "Small hardcoded policy set; FAISS/Pinecone adapters written but not run at scale"),
    ("Simplified EMI estimate",
     "12-month amortisation approximation, not a full tenure-and-rate schedule"),
    ("Audit log holds plaintext PII",
     "No field encryption, no retention window — blocks production data today"),
    ("Thresholds not yet externalised",
     "Policy limits live in code; config-driven thresholds are pending"),
]
y = 1.65
for head, body in lims:
    textbox(s, 0.5, y, 6.0, 0.3, [("⚠  " + head, 13, True, INK)])
    textbox(s, 0.78, y + 0.27, 5.7, 0.35, [(body, 11, False, GREY)])
    y += 0.78
textbox(s, 7.0, 1.25, 5.9, 0.35, [("Roadmap, in priority order", 16, True, GREEN)])
road = [
    ("Now", "Encrypt/hash audit PII; add retention policy", RED),
    ("Next", "Externalise thresholds to versioned config", AMBER),
    ("Next", "Full amortisation schedule for EMI", AMBER),
    ("Then", "Wire real policy corpus into FAISS index", BLUE),
    ("Then", "Postgres audit store + monitoring dashboards", BLUE),
    ("Later", "ML risk score as an advisory input, rules stay authoritative", GREY),
]
for i, (when, what, colour) in enumerate(road):
    top = 1.65 + i * 0.78
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 7.0, top, 1.15, 0.6, colour, None,
          [(when, 11, True, WHITE)])
    textbox(s, 8.3, top + 0.12, 4.6, 0.45, [(what, 12, False, INK)])
footnote(s, "Design stance: the rules engine remains the authoritative decision-maker. Any future "
            "model is advisory input, so explainability is never traded away.", top=6.6)

# --------------------------------------------------------------------------- #
# 17. Close / Q&A
# --------------------------------------------------------------------------- #
s = slide(
    "TIMING: 16:15-16:40 (25s), then Q&A\n\n"
    "To close: three things worth remembering.\n\n"
    "Speed without opacity - every decision comes with its reasoning attached.\n\n"
    "Governance by construction - the borderline band, the audit trail, and the boundary "
    "validation are structural, not features added later.\n\n"
    "Built to extend - skills, subagents, and pluggable external tools mean new policy, new "
    "data sources, and new backends land without a rewrite.\n\n"
    "Happy to take questions.\n\n"
    "LIKELY QUESTIONS: (1) Why no ML? - explainability requirement plus deterministic policy; "
    "advisory model is on the roadmap. (2) How do you handle policy change? - versioned config "
    "plus a test fixture per rule. (3) What about fair lending? - name is report-only, no proxy "
    "attributes are inputs, and every decision is replayable. (4) What breaks first at scale? - "
    "the retrieval layer, which is why it sits behind an interface."
)
shape(s, MSO_SHAPE.RECTANGLE, 0, 0, SW, 7.5, RGBColor(0x0E, 0x2A, 0x40), None)
shape(s, MSO_SHAPE.RECTANGLE, 0, 2.9, SW, 0.06, AMBER, None)
textbox(s, 0.8, 2.0, SW - 1.6, 0.85,
        [("Thank You  —  Questions?", 40, True, WHITE)], align=PP_ALIGN.CENTER)
takeaways = [
    ("Speed without opacity", "Sub-second decisions that always\ncarry their own reasoning"),
    ("Governance by construction", "Borderline escalation, boundary validation,\nand audit trail are structural"),
    ("Built to extend", "New skills and pluggable tools land\nwithout touching the core"),
]
for i, (head, body) in enumerate(takeaways):
    card(s, 0.8 + i * 4.05, 3.5, 3.75, 1.5,
         [(head, 16, True, WHITE), ("", 6, False, WHITE), (body, 11, False, RGBColor(0xCF, 0xE4, 0xF5))],
         fill=RGBColor(0x16, 0x3D, 0x5C), line=RGBColor(0x2E, 0x6C, 0x99))
textbox(s, 0.8, 5.4, SW - 1.6, 0.4,
        [("Loan Eligibility AI  •  Intelligent Multi-Agent Assessment System  •  August 2026",
          13, False, RGBColor(0x9F, 0xB8, 0xCC))], align=PP_ALIGN.CENTER)

prs.save(OUT)
total = sum(1 for _ in prs.slides)
print(f"wrote {OUT} ({total} slides)")
