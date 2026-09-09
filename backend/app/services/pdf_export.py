"""
Generate a question paper PDF (question paper + answer key) using WeasyPrint.
"""

from __future__ import annotations
import re
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.papers import Paper, PaperQuestion

_SUP_MAP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

SECTION_DISPLAY = {
    "A": "Multiple Choice Questions",
    "B": "Very Short Answer",
    "C": "Short Answer",
    "D": "Long Answer",
    "E": "Case Based",
}


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _fix_math(text: str) -> str:
    """Convert caret-notation and common MathML-strip artifacts to Unicode."""
    # x^2 → x², x^{10} → x¹⁰
    def sup_replace(m: re.Match) -> str:
        return m.group(1) + m.group(2).translate(_SUP_MAP)

    text = re.sub(r'([A-Za-z0-9\)\]])\s*\^\s*\{?([0-9]+)\}?', sup_replace, text)
    # Also handle plain "x 2 " after bracket/letter when followed by space+operator or end
    # (conservative — only when preceded by ) or ] to avoid false positives)
    text = re.sub(r'([\)\]])\s+([0-9])\s*(?=[+\-×÷=\s,\.])', sup_replace, text)
    return text


def _strip_answer_prefix(text: str) -> str:
    """Remove leading 'Answer:' or 'Ans:' label from DB answer text."""
    stripped = text.strip()
    for prefix in ("answer:", "ans:", "answer :", "ans :"):
        if stripped.lower().startswith(prefix):
            stripped = stripped[len(prefix):].lstrip()
            break
    return stripped


def _extract_mcq_options(question_text: str) -> tuple[str, list[dict] | None]:
    """
    If the question text embeds MCQ options as (A) ... (B) ... (C) ... (D) ...,
    split them out and return (stem, options_list). Otherwise return (text, None).
    """
    idx = question_text.find("(A)")
    if idx == -1:
        return question_text, None
    stem = question_text[:idx].strip()
    tail = question_text[idx:]
    # Split on option markers: (A), (B), (C), (D)
    parts = re.split(r'\(([A-D])\)', tail)
    # parts = ['', 'A', 'text_a', 'B', 'text_b', 'C', 'text_c', 'D', 'text_d', ...]
    options = []
    i = 1
    while i + 1 < len(parts):
        key = parts[i].strip()
        val = parts[i + 1].strip()
        if key in ("A", "B", "C", "D"):
            options.append({"key": key, "text": val})
        i += 2
    if len(options) < 3:
        return question_text, None
    return stem, options


def _option_rows(options: list[dict]) -> str:
    items = "".join(
        f"<span class='opt'>({o['key']})&nbsp;{_html_escape(_fix_math(str(o['text'])))}</span>"
        for o in options
    )
    return f"<div class='options'>{items}</div>"


def build_paper_html(
    paper: "Paper",
    paper_questions: list["PaperQuestion"],
    institute_name: str,
    exam_date: str | None = None,
) -> str:
    today = exam_date or date.today().strftime("%d %B %Y")
    section_label = f"Section {paper.section}" if paper.section else ""
    header_sub = f"{paper.board} | Class {paper.class_} {section_label}".strip(" |")

    # Group questions by section
    sections: dict[str, list] = {}
    for pq in sorted(paper_questions, key=lambda x: (x.section_label, x.question_order)):
        sections.setdefault(pq.section_label, []).append(pq)

    # ── Question paper body ────────────────────────────────────────────────────
    q_body = ""
    q_global = 1
    for sec_label, pqs in sections.items():
        first_pq = pqs[0]
        mpc = first_pq.marks
        count = len(pqs)
        sec_marks = mpc * count

        sec_name = SECTION_DISPLAY.get(sec_label, first_pq.question.question_type)
        q_word = "question" if count == 1 else "questions"
        m_word = "mark" if mpc == 1 else "marks"
        t_word = "mark" if sec_marks == 1 else "marks"

        q_body += f"""
        <div class='section-header'>
            Section {sec_label} — {sec_name} &nbsp;
            <span class='sec-meta'>({count} {q_word} × {mpc} {m_word} = {sec_marks} {t_word})</span>
        </div>"""

        for pq in pqs:
            q = pq.question
            raw_text = _fix_math(q.question_text)

            # Extract inline MCQ options when DB options field is empty
            if q.question_type == "MCQ" and not q.options:
                stem, parsed_opts = _extract_mcq_options(raw_text)
            else:
                stem, parsed_opts = raw_text, None

            q_body += f"""
            <div class='question'>
                <span class='q-num'>Q{q_global}.</span>
                <span class='q-text'>{_html_escape(stem)}</span>
                <span class='q-marks'>[{pq.marks}M]</span>
            </div>"""

            if q.question_type == "MCQ":
                opts = parsed_opts or (q.options if q.options else None)
                if opts:
                    q_body += _option_rows(opts)
            else:
                lines = max(2, pq.marks * 2)
                q_body += f"<div class='answer-space' style='height:{lines * 18}px'></div>"
            q_global += 1

    # ── Answer key body ────────────────────────────────────────────────────────
    ak_body = "<table class='ak-table'><thead><tr><th>Q#</th><th>Section</th><th>Type</th><th>Marks</th><th>Answer</th></tr></thead><tbody>"
    q_num = 1
    for sec_label, pqs in sections.items():
        for pq in pqs:
            q = pq.question
            sec_name = SECTION_DISPLAY.get(sec_label, q.question_type)
            raw_answer = _strip_answer_prefix(str(q.answer or ""))
            answer_text = _html_escape(_fix_math(raw_answer))
            ak_body += f"<tr><td>{q_num}</td><td>{sec_label}</td><td>{sec_name}</td><td>{pq.marks}</td><td class='ak-ans'>{answer_text}</td></tr>"
            q_num += 1
    ak_body += "</tbody></table>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 18mm 20mm;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Times New Roman', Times, serif;
    font-size: 11pt;
    color: #111;
    line-height: 1.5;
  }}
  .institute {{ text-align: center; font-size: 15pt; font-weight: bold; margin-bottom: 2pt; }}
  .paper-title {{ text-align: center; font-size: 13pt; font-weight: bold; margin-bottom: 2pt; }}
  .meta-row {{ text-align: center; font-size: 10pt; color: #444; margin-bottom: 6pt; }}
  .divider {{ border: none; border-top: 1.5px solid #222; margin: 6pt 0; }}
  .instructions {{
    font-size: 9.5pt; color: #333;
    margin-bottom: 10pt;
    padding: 5pt 8pt;
    border: 1px solid #bbb;
    border-radius: 3pt;
  }}
  .section-header {{
    font-weight: bold; font-size: 11pt;
    margin: 12pt 0 4pt 0;
    border-bottom: 1px solid #aaa;
    padding-bottom: 2pt;
  }}
  .sec-meta {{ font-weight: normal; font-size: 9.5pt; color: #555; }}
  .question {{
    display: flex; gap: 6pt;
    margin: 6pt 0 2pt 0;
  }}
  .q-num {{ font-weight: bold; white-space: nowrap; min-width: 22pt; }}
  .q-text {{ flex: 1; }}
  .q-marks {{ color: #666; font-size: 9.5pt; white-space: nowrap; align-self: flex-start; }}
  .options {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 2pt 10pt;
    margin: 2pt 0 6pt 28pt;
    font-size: 10.5pt;
  }}
  .opt {{ display: block; }}
  .answer-space {{
    margin: 4pt 0 4pt 28pt;
    border-bottom: 1px dotted #bbb;
  }}
  /* Answer key */
  .page-break {{ page-break-before: always; }}
  .ak-title {{ font-size: 14pt; font-weight: bold; text-align: center; margin-bottom: 10pt; }}
  .ak-table {{ width: 100%; border-collapse: collapse; font-size: 10pt; }}
  .ak-table th, .ak-table td {{ border: 1px solid #ccc; padding: 4pt 6pt; }}
  .ak-table th {{ background: #eee; font-weight: bold; text-align: left; }}
  .ak-ans {{ max-width: 260pt; word-break: break-word; }}
</style>
</head>
<body>

<!-- ═══════════════════════ QUESTION PAPER ═══════════════════════ -->
<div class='institute'>{_html_escape(institute_name)}</div>
<div class='paper-title'>{_html_escape(paper.title)}</div>
<div class='meta-row'>{_html_escape(header_sub)} &nbsp;|&nbsp; Total Marks: {paper.total_marks} &nbsp;|&nbsp; Date: {today}</div>
<hr class='divider'>
<div class='instructions'>
  <strong>General Instructions:</strong>
  (1) All questions are compulsory.
  (2) Section A contains MCQs of 1 mark each.
  (3) Read all questions carefully before answering.
  (4) Write answers clearly in the space provided.
</div>

{q_body}

<!-- ═══════════════════════ ANSWER KEY ═══════════════════════ -->
<div class='page-break'></div>
<div class='ak-title'>Answer Key — {_html_escape(paper.title)}</div>
<div class='meta-row'>{_html_escape(header_sub)} &nbsp;|&nbsp; Total Marks: {paper.total_marks} &nbsp;|&nbsp; Date: {today}</div>
<hr class='divider'>
{ak_body}

</body>
</html>"""

    return html


def generate_pdf(html: str) -> bytes:
    from weasyprint import HTML, CSS
    return HTML(string=html).write_pdf()
