"""Capture screenshots of the running Loan Eligibility AI app for the deck.

Prerequisites: backend on :8000 and Streamlit on :8501 already running.

    python docs/capture_screenshots.py

Writes PNGs into docs/screenshots/. A tall viewport is used deliberately:
Streamlit scrolls inside its own container, so `full_page=True` only ever
captures one viewport. Rendering everything at once and cropping by element
bounding box gives clean, slide-ready sections instead.
"""

import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

UI = "http://localhost:8501"
API = "http://localhost:8000"

VIEWPORT = {"width": 1600, "height": 3000}
SCALE = 2
SETTLE = 700  # ms to let a Streamlit rerun finish


def grab(page):
    """Current viewport as a PIL image."""
    return Image.open(io.BytesIO(page.screenshot()))


def trim_bottom(img, keep=24):
    """Drop uniform-colour rows at the bottom so crops end at real content."""
    px = img.convert("RGB")
    w, h = px.size
    bg = px.getpixel((w - 2, h - 2))
    row = h
    while row > 1:
        line = px.crop((0, row - 1, w, row)).getcolors(maxcolors=w * 2)
        if line and len(line) == 1 and line[0][1] == bg:
            row -= 1
        else:
            break
    return img.crop((0, 0, w, min(h, row + keep)))


def save(img, name, trim=True):
    if trim:
        img = trim_bottom(img)
    img.save(OUT / name)
    print("  wrote", name, img.size)


def shot(page, name):
    save(grab(page), name)


def region(page, name, top, bottom=None, pad=18, left_sel=None):
    """Crop the viewport between two elements' vertical bounds."""
    top_box = top.bounding_box()
    if top_box is None:
        print("  skip", name, "(top element not visible)")
        return
    y0 = max(top_box["y"] - pad, 0)
    if bottom is not None:
        bot_box = bottom.bounding_box()
        y1 = (bot_box["y"] + bot_box["height"] + pad) if bot_box else y0 + 900
    else:
        y1 = y0 + 900

    ref = (left_sel or top).bounding_box()
    x0 = max(ref["x"] - pad, 0)
    x1 = min(ref["x"] + ref["width"] + pad, VIEWPORT["width"])

    img = grab(page)
    box = tuple(int(v * SCALE) for v in (x0, y0, x1, min(y1, VIEWPORT["height"])))
    save(img.crop(box), name)


def sidebar_region(page, name, from_text, pad=14):
    """Screenshot the sidebar, then crop from a heading down to its content end.

    The sidebar scrolls independently, so coordinates are resolved inside the
    page against the sidebar's own content box rather than the viewport.
    """
    sidebar = page.locator("section[data-testid='stSidebar']")
    raw = Image.open(io.BytesIO(sidebar.screenshot()))
    top = page.evaluate(
        """(needle) => {
            const sb = document.querySelector("section[data-testid='stSidebar']");
            const heads = [...sb.querySelectorAll('h1,h2,h3,h4,p,div')];
            const el = heads.find(e => e.textContent.trim().startsWith(needle));
            if (!el) return null;
            let y = 0, node = el;
            while (node && node !== sb) { y += node.offsetTop || 0; node = node.offsetParent; }
            return y;
        }""",
        from_text,
    )
    if top is None:
        save(raw, name)
        return
    y0 = max(int((top - pad) * SCALE), 0)
    save(raw.crop((0, y0, raw.width, raw.height)), name)


def set_text(page, label, value):
    box = page.get_by_label(label, exact=True)
    box.fill(str(value))
    box.press("Enter")
    page.wait_for_timeout(SETTLE)


def set_number(page, label, value):
    box = page.get_by_label(label, exact=True)
    box.click(force=True)
    box.press("Control+a")
    box.type(str(value))
    box.press("Enter")
    page.wait_for_timeout(SETTLE)


def select_employment(page, value):
    page.get_by_label("Employment Type *", exact=True).click(force=True)
    page.wait_for_timeout(400)
    page.get_by_text(value, exact=True).last.click()
    page.wait_for_timeout(SETTLE)


def fill_application(page, name, age, employment, income, emi, credit, loan):
    set_text(page, "Full Name *", name)
    set_number(page, "Age *", age)
    select_employment(page, employment)
    set_number(page, "Monthly Income (₹) *", income)
    set_number(page, "Existing EMI (₹) *", emi)
    set_number(page, "Credit Score *", credit)
    set_number(page, "Loan Amount Required (₹) *", loan)


def evaluate(page):
    page.get_by_role("button", name="⚡ Evaluate Eligibility").click()
    page.wait_for_timeout(3000)


def clear_form(page):
    page.get_by_role("button", name="🔄 Clear Form").click()
    page.wait_for_timeout(SETTLE + 500)


def ask(page, question):
    field = page.get_by_placeholder("e.g. What credit score do I need?")
    field.fill(question)
    field.press("Enter")
    page.wait_for_timeout(2500)


def heading(page, text):
    return page.locator("h3, h4", has_text=text).first


def main():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        except Exception:
            browser = p.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
        ctx = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=SCALE,
            accept_downloads=True,
        )
        page = ctx.new_page()
        sidebar = page.locator("section[data-testid='stSidebar']")

        print("01 landing page")
        page.goto(UI, wait_until="networkidle")
        page.wait_for_timeout(5000)
        shot(page, "01_landing.png")

        print("02 form filled (eligible applicant)")
        fill_application(page, "Ankita Vyas", 34, "salaried", 95000, 8000, 762, 300000)
        region(
            page,
            "02_form_filled.png",
            heading(page, "Enter Your Information"),
            page.get_by_role("button", name="⚡ Evaluate Eligibility"),
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )

        print("03 eligible decision")
        evaluate(page)
        shot(page, "03_result_eligible_full.png")
        region(
            page,
            "03_result_eligible.png",
            heading(page, "Assessment Complete"),
            heading(page, "Eligibility Assessment"),
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )
        region(
            page,
            "04_reasoning_and_recommendations.png",
            heading(page, "Eligibility Assessment"),
            heading(page, "Supporting Policy References"),
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )

        print("05 pdf download")
        try:
            with page.expect_download(timeout=15000) as dl:
                page.get_by_role("button", name="📥 Download Assessment Report (PDF)").click()
            dl.value.save_as(str(OUT / "report_eligible.pdf"))
            print("  wrote report_eligible.pdf")
        except Exception as exc:
            print("  PDF download failed:", exc)

        print("06 chatbot answering about this result")
        ask(page, "Why am I eligible?")
        ask(page, "What is my EMI ratio?")
        ask(page, "What documents will I need?")
        sidebar_region(page, "06_chat_sidebar.png", "💬 Ask the Loan Assistant")

        print("07 chatbot safety guard + out of scope")
        page.get_by_role("button", name="🧹 Clear chat").click()
        page.wait_for_timeout(SETTLE)
        ask(page, "My card number is 4111 1111 1111 1111 - am I approved?")
        ask(page, "What is the weather in Bangalore today?")
        sidebar_region(page, "07_chat_safety.png", "💬 Ask the Loan Assistant")

        print("08 needs manual review")
        clear_form(page)
        fill_application(page, "Shubham Kumar", 38, "self-employed", 70000, 4000, 695, 300000)
        evaluate(page)
        region(
            page,
            "08_result_manual_review.png",
            heading(page, "Assessment Complete"),
            heading(page, "Eligibility Assessment"),
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )
        region(
            page,
            "08b_manual_review_recommendations.png",
            heading(page, "Eligibility Assessment"),
            heading(page, "Supporting Policy References"),
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )

        print("09 not eligible")
        clear_form(page)
        fill_application(page, "Vandana H K", 29, "other", 50000, 10000, 640, 600000)
        evaluate(page)
        region(
            page,
            "09_result_not_eligible.png",
            heading(page, "Assessment Complete"),
            heading(page, "Eligibility Assessment"),
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )
        region(
            page,
            "09b_not_eligible_recommendations.png",
            heading(page, "Improvement Recommendations"),
            heading(page, "Supporting Policy References"),
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )

        # A reload is required, not "Clear Form": Streamlit keeps widget state
        # keyed by widget key, so the form's own reset does not empty the inputs.
        print("10 validation errors (on a freshly loaded form)")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(5000)
        evaluate(page)
        region(
            page,
            "10_validation_errors.png",
            heading(page, "Loan Details"),
            page.locator("div.error-card, div.info-box").last,
            left_sel=page.locator("div[data-testid='stMainBlockContainer']").first,
        )

        print("11 FastAPI docs")
        api = ctx.new_page()
        api.set_viewport_size({"width": 1600, "height": 1400})
        api.goto(f"{API}/docs", wait_until="networkidle")
        api.wait_for_timeout(2500)
        api.screenshot(path=str(OUT / "11_api_docs.png"))
        print("  wrote 11_api_docs.png")

        print("12 /process endpoint expanded")
        try:
            api.locator("#operations-default-process_application_process_post").click()
            api.wait_for_timeout(1500)
            api.screenshot(path=str(OUT / "12_api_process_endpoint.png"))
            print("  wrote 12_api_process_endpoint.png")
        except Exception as exc:
            print("  endpoint expand failed:", exc)

        print("13 audit trail console view")
        console = ctx.new_page()
        console.set_viewport_size({"width": 1500, "height": 780})
        console.set_content(build_console_html())
        console.wait_for_timeout(600)
        console.locator("body").screenshot(path=str(OUT / "13_audit_trail.png"))
        print("  wrote 13_audit_trail.png")

        browser.close()

    render_pdf_pages()
    print("done")


def build_console_html():
    """A terminal-styled page showing the real curl call and real audit lines."""
    import json
    import subprocess

    payload = {
        "name": "Ankita Vyas", "age": 34, "monthly_income": 95000,
        "existing_emi": 8000, "credit_score": 762,
        "employment_type": "salaried", "loan_amount_required": 300000,
    }
    try:
        import requests
        resp = requests.post(f"{API}/process", json=payload, timeout=10).json()
        # The three evidence snippets are elided so the response stays legible
        # when this image is placed on a slide; the elision is labelled.
        evidence = resp.pop("rag_evidence", [])
        body = json.dumps(resp, indent=2)[:-2].rstrip().rstrip(",")
        ids = ", ".join(d.get("id", "?") for d in evidence)
        body += f',\n  "rag_evidence": [ {ids} ]   // 3 snippets, text elided\n}}'
    except Exception as exc:
        body = f"(service unreachable: {exc})"

    audit_path = Path(__file__).parent.parent / "logs" / "audit.log"
    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()[-2:]
    audit = "\n\n".join(lines)

    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:warnings"],
        capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
    ).stdout.strip().splitlines()
    tests = "\n".join(tests[-1:]) or "(pytest not run)"

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    short_payload = json.dumps(payload)[:96] + " ... }'"
    return f"""
<html><head><meta charset="utf-8"><style>
  body {{ margin:0; background:#12141c; color:#d7dbe6; font-family:'DejaVu Sans Mono',monospace;
          font-size:19px; padding:30px 34px; }}
  .p {{ color:#7bd88f; }} .c {{ color:#8b93a7; }} .k {{ color:#f0c674; }}
  h2 {{ font-family:'Ubuntu',sans-serif; font-size:18px; color:#9aa4bf; margin:0 0 10px;
        text-transform:uppercase; letter-spacing:.12em; }}
  pre {{ margin:0 0 26px; white-space:pre-wrap; line-height:1.45; }}
</style></head><body>
<h2>1 &nbsp;API call</h2>
<pre><span class="p">$</span> curl -s -X POST localhost:8000/process -d '{esc(short_payload)}
{esc(body)}</pre>
<h2>2 &nbsp;logs/audit.log — one JSON line per decision</h2>
<pre>{esc(audit)}</pre>
<h2>3 &nbsp;Test suite</h2>
<pre><span class="p">$</span> pytest -q
<span class="k">{esc(tests)}</span></pre>
</body></html>"""


def render_pdf_pages():
    """Render the downloaded PDF report to PNG so it can go on a slide."""
    pdf = OUT / "report_eligible.pdf"
    if not pdf.exists():
        print("  no PDF to render")
        return
    try:
        import pymupdf
    except ImportError:
        print("  pymupdf not installed; skipping PDF render")
        return
    doc = pymupdf.open(pdf)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=170)
        name = f"14_pdf_report_p{i + 1}.png"
        pix.save(str(OUT / name))
        print("  wrote", name, (pix.width, pix.height))


if __name__ == "__main__":
    sys.exit(main())
