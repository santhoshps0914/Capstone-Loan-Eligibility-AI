"""Capture the four result screenshots used on the 'Screenshots of Results' slide.

Requires the backend (:8000) and the Streamlit UI (:8501) to be running.
Writes PNGs into assets/screenshots/.
"""
import json
import os
import time
import uuid

import requests
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "screenshots")
UI = "http://127.0.0.1:8501"
API = "http://127.0.0.1:8000"

APPLICANT = {
    "name": "Asha Menon",
    "age": 34,
    "monthly_income": 150000.0,
    "existing_emi": 5000.0,
    "credit_score": 780,
    "employment_type": "salaried",
    "loan_amount_required": 300000.0,
}


def fill_form(page):
    """Type the applicant into the Streamlit form and wait for it to settle."""
    page.goto(UI, wait_until="networkidle")
    page.wait_for_selector("text=Enter Your Information", timeout=60000)

    def set_field(label, value):
        box = page.get_by_label(label, exact=True)
        box.click()
        box.fill("")
        box.type(str(value), delay=20)
        box.press("Tab")
        page.wait_for_timeout(400)

    set_field("Full Name *", APPLICANT["name"])
    set_field("Age *", APPLICANT["age"])
    page.get_by_label("Employment Type *", exact=True).click()
    page.get_by_text(APPLICANT["employment_type"], exact=True).click()
    page.wait_for_timeout(500)
    set_field("Monthly Income (₹) *", int(APPLICANT["monthly_income"]))
    set_field("Existing EMI (₹) *", int(APPLICANT["existing_emi"]))
    set_field("Credit Score *", APPLICANT["credit_score"])
    set_field("Loan Amount Required (₹) *", int(APPLICANT["loan_amount_required"]))
    page.wait_for_timeout(1200)


def hide_chrome(page):
    """Drop the Streamlit toolbar/sidebar so the frame is just the app content."""
    page.add_style_tag(content="""
      [data-testid="stToolbar"], [data-testid="stDecoration"],
      [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
      header { display: none !important; }
      [data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }
    """)
    page.wait_for_timeout(400)


def clip_of(page, first, last, pad=24):
    """Crop to the vertical span of two locators, at full content width.

    Horizontal extent comes from the Streamlit block container so multi-column
    layouts are never sliced in half.
    """
    a = first.bounding_box()
    b = last.bounding_box()
    top = min(a["y"], b["y"]) - pad
    bottom = max(a["y"] + a["height"], b["y"] + b["height"]) + pad
    box = page.locator('[data-testid="stMainBlockContainer"], '
                       '.block-container').first.bounding_box()
    return {"x": max(box["x"] - pad, 0), "y": max(top, 0),
            "width": box["width"] + 2 * pad, "height": bottom - top}


def shot_form_and_decision(page):
    # Streamlit scrolls an inner container, so full_page screenshots only ever
    # capture one viewport. A tall viewport puts the whole result in view
    # instead, which makes clip coordinates and bounding boxes agree.
    page.set_viewport_size({"width": 1440, "height": 2600})
    fill_form(page)
    hide_chrome(page)
    page.screenshot(
        path=os.path.join(OUT, "01_application_form.png"),
        clip=clip_of(page,
                     page.get_by_text("Enter Your Information"),
                     page.get_by_role("button", name="⚡ Evaluate Eligibility")),
    )
    print("saved 01_application_form.png")

    page.get_by_role("button", name="⚡ Evaluate Eligibility").click()
    page.wait_for_selector("text=Assessment Complete", timeout=60000)
    page.wait_for_selector("text=Eligibility Assessment", timeout=60000)
    page.wait_for_timeout(1500)
    hide_chrome(page)
    # Frame the decision panel: verdict banner through the per-rule reasoning.
    page.screenshot(
        path=os.path.join(OUT, "02_decision_panel.png"),
        clip=clip_of(page,
                     page.get_by_text("Assessment Complete"),
                     page.get_by_text("emi_ratio:").first),
    )
    print("saved 02_decision_panel.png")


def shot_pdf():
    """Render the real ReportLab PDF's first page to a PNG."""
    import sys

    import pypdfium2 as pdfium

    sys.path.insert(0, ROOT)
    from ui.app import generate_pdf  # noqa: E402

    resp = requests.post(
        f"{API}/process",
        json=APPLICANT,
        headers={"X-Request-ID": str(uuid.uuid4())},
        timeout=10,
    ).json()

    pdf_bytes = generate_pdf(APPLICANT, resp, APPLICANT["credit_score"])
    if hasattr(pdf_bytes, "getvalue"):
        pdf_bytes = pdf_bytes.getvalue()

    doc = pdfium.PdfDocument(pdf_bytes)
    img = doc[0].render(scale=2.5).to_pil().convert("RGB")

    # The report only fills the top third of an A4 page — trim the trailing
    # whitespace (keeping the footer line) so the slide frame isn't mostly blank.
    from PIL import ImageChops, Image as PILImage

    bg = PILImage.new("RGB", img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        # Rows that contain ink, then cut at the first gap taller than ~1 inch —
        # that gap is the dead space between the body and the page footer.
        inked = [y for y in range(bbox[1], bbox[3])
                 if diff.crop((0, y, img.width, y + 1)).getbbox()]
        end = inked[-1]
        gap = int(2.5 * 72)
        for prev, nxt in zip(inked, inked[1:]):
            if nxt - prev > gap:
                end = prev
                break
        pad = 40
        img = img.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                        min(bbox[2] + pad, img.width),
                        min(end + pad, img.height)))
    img.save(os.path.join(OUT, "03_pdf_report.png"))
    print("saved 03_pdf_report.png")


VARIANTS = [
    # One of each outcome, so the trail shows the full decision range.
    dict(APPLICANT),
    dict(APPLICANT, name="Rohit Sharma", credit_score=698, existing_emi=34000.0),
    dict(APPLICANT, name="Vikram Iyer", credit_score=610, monthly_income=45000.0),
]


def seed_audit_trail():
    """Drive one request per outcome so the audit tail isn't four identical rows."""
    for payload in VARIANTS:
        requests.post(f"{API}/process", json=payload,
                      headers={"X-Request-ID": str(uuid.uuid4())}, timeout=10)
        time.sleep(0.2)


def shot_audit(page):
    """Render the tail of the real audit log as a terminal-style capture."""
    seed_audit_trail()
    path = os.path.join(ROOT, "logs", "audit.log")
    with open(path) as fh:
        lines = [ln.strip() for ln in fh if ln.strip()][-len(VARIANTS):]

    # One compact line per record so the frame stays readable on a slide.
    body = "\n\n".join(json.dumps(json.loads(ln)) for ln in lines)

    html = """<!doctype html><meta charset="utf-8">
<style>
  body {{ margin:0; background:#0d1117; font-family:'DejaVu Sans Mono',monospace; }}
  .bar {{ background:#161b22; color:#8b949e; padding:10px 16px; font-size:15px;
          border-bottom:1px solid #30363d; }}
  pre {{ color:#c9d1d9; font-size:14px; line-height:1.55; padding:16px 20px;
         margin:0; white-space:pre-wrap; word-break:break-all; }}
  .k {{ color:#79c0ff; }}
</style>
<div class="bar">$ tail -f logs/audit.log&nbsp;&nbsp;—&nbsp;&nbsp;append-only decision trail</div>
<pre>{body}</pre>""".format(body=body)

    page.set_viewport_size({"width": 1100, "height": 400})
    page.set_content(html)
    page.wait_for_timeout(400)
    # Shrink the viewport to the rendered text so there's no dead space.
    height = page.evaluate("document.documentElement.scrollHeight")
    page.set_viewport_size({"width": 1100, "height": int(height)})
    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(OUT, "04_audit_trail.png"))
    print("saved 04_audit_trail.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000},
                                device_scale_factor=2)
        shot_form_and_decision(page)
        shot_audit(page)
        browser.close()
    shot_pdf()


if __name__ == "__main__":
    main()
