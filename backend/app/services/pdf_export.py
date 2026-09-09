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

_FIGURE_KEYWORDS = re.compile(
    r'\b(given figure|figure shown|figure below|in the figure|as shown|from the figure|'
    r'the figure|refer to figure|see figure)\b',
    re.IGNORECASE,
)


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _fix_math(text: str) -> str:
    """Convert caret-notation and common MathML-strip artifacts to Unicode."""
    def sup_replace(m: re.Match) -> str:
        return m.group(1) + m.group(2).translate(_SUP_MAP)

    text = re.sub(r'([A-Za-z0-9\)\]])\s*\^\s*\{?([0-9]+)\}?', sup_replace, text)
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
    Split embedded MCQ options from question text.
    Handles two formats:
      - Regular MCQ: stem ... (A) opt_a (B) opt_b (C) opt_c (D) opt_d
      - Assertion-Reason: Assertion (A): [text] Reason (R): [text]
            (A) Both A and R are true ... (B) ... (C) ... (D) ...
    """
    text = question_text

    # Assertion-Reason: look for the standard "(A) Both" start of options
    is_assertion = bool(re.search(r'\bAssertion\b', text, re.IGNORECASE))
    if is_assertion:
        # Find where the actual A/B/C/D answer choices begin
        match = re.search(r'\(A\)\s*Both\b', text, re.IGNORECASE)
        if not match:
            # Try finding any "(A)" that comes after Reason
            reason_pos = text.lower().find("reason")
            if reason_pos != -1:
                match = re.search(r'\(A\)', text[reason_pos:])
                if match:
                    match = type('obj', (object,), {
                        'start': lambda self: reason_pos + match.start()
                    })()
        if match:
            split_pos = match.start() if callable(match.start) else match.start()
            stem = text[:split_pos].strip()
            tail = text[split_pos:]
            parts = re.split(r'\(([A-D])\)', tail)
            options = []
            i = 1
            while i + 1 < len(parts):
                key = parts[i].strip()
                val = parts[i + 1].strip()
                if key in ("A", "B", "C", "D"):
                    options.append({"key": key, "text": val})
                i += 2
            if len(options) >= 3:
                return stem, options
        return text, None

    # Regular MCQ: split at first (A) that isn't preceded by "Assertion"
    idx = text.find("(A)")
    if idx == -1:
        return text, None
    stem = text[:idx].strip()
    tail = text[idx:]
    parts = re.split(r'\(([A-D])\)', tail)
    options = []
    i = 1
    while i + 1 < len(parts):
        key = parts[i].strip()
        val = parts[i + 1].strip()
        if key in ("A", "B", "C", "D"):
            options.append({"key": key, "text": val})
        i += 2
    if len(options) < 3:
        return text, None
    return stem, options


def _option_rows(options: list[dict], is_assertion: bool = False) -> str:
    if is_assertion:
        # Assertion-Reason options are long sentences — render as single column list
        items = "".join(
            f"<div class='ar-opt'>({o['key']})&nbsp;{_html_escape(_fix_math(str(o['text'])))}</div>"
            for o in options
        )
        return f"<div class='ar-options'>{items}</div>"
    items = "".join(
        f"<span class='opt'>({o['key']})&nbsp;{_html_escape(_fix_math(str(o['text'])))}</span>"
        for o in options
    )
    return f"<div class='options'>{items}</div>"


def _figure_note(text: str) -> str:
    """Return a figure-missing notice if the question references a figure."""
    if _FIGURE_KEYWORDS.search(text):
        return "<div class='fig-note'>[Figure required — refer to the original textbook]</div>"
    return ""


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
            is_assertion = bool(re.search(r'\bAssertion\b', raw_text, re.IGNORECASE))

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
                    q_body += _option_rows(opts, is_assertion=is_assertion)
                q_body += _figure_note(stem)
            else:
                q_body += _figure_note(raw_text)
                lines = max(2, pq.marks * 2)
                q_body += f"<div class='answer-space' style='height:{lines * 18}px'></div>"
            q_global += 1

    # ── Answer key body ────────────────────────────────────────────────────────
    # Part A: MCQ quick-reference grid (Section A only, compact)
    mcq_rows = []
    detail_blocks = []
    q_num = 1

    for sec_label, pqs in sections.items():
        sec_name = SECTION_DISPLAY.get(sec_label, "")
        for pq in pqs:
            q = pq.question
            raw_answer = _strip_answer_prefix(str(q.answer or ""))
            answer_text = _html_escape(_fix_math(raw_answer))

            if sec_label == "A":
                # Extract just the answer letter if present
                letter_match = re.match(r'^\(([A-D])\)', raw_answer.strip())
                letter = f"({letter_match.group(1)})" if letter_match else raw_answer[:8].strip()
                mcq_rows.append((q_num, letter))
            else:
                detail_blocks.append({
                    "num": q_num,
                    "marks": pq.marks,
                    "sec": sec_label,
                    "sec_name": sec_name,
                    "answer": answer_text,
                })
            q_num += 1

    # Build MCQ grid HTML (5 columns)
    ak_mcq = ""
    if mcq_rows:
        ak_mcq = "<div class='ak-mcq-title'>Section A — Quick Reference</div>"
        ak_mcq += "<table class='ak-mcq'><tbody>"
        chunk = 5
        for row_start in range(0, len(mcq_rows), chunk):
            row_items = mcq_rows[row_start:row_start + chunk]
            ak_mcq += "<tr>"
            for qn, letter in row_items:
                ak_mcq += f"<td><b>Q{qn}</b></td><td class='ak-letter'>{_html_escape(letter)}</td>"
            # pad incomplete row
            for _ in range(chunk - len(row_items)):
                ak_mcq += "<td></td><td></td>"
            ak_mcq += "</tr>"
        ak_mcq += "</tbody></table>"

    # Build detailed answer blocks HTML
    ak_detail = ""
    if detail_blocks:
        ak_detail = "<div class='ak-detail-title'>Sections B – E — Detailed Answers</div>"
        for blk in detail_blocks:
            ak_detail += f"""
            <div class='ak-block'>
                <div class='ak-q-header'>Q{blk['num']}. &nbsp;[{blk['marks']}M — {blk['sec_name']}]</div>
                <div class='ak-q-answer'>{blk['answer']}</div>
            </div>"""

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
    line-height: 1.55;
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
    display: flex; gap: 0;
    margin: 6pt 0 2pt 0;
    align-items: flex-start;
  }}
  .q-num {{
    font-weight: bold;
    white-space: nowrap;
    min-width: 34pt;
    padding-right: 4pt;
    flex-shrink: 0;
  }}
  .q-text {{ flex: 1; }}
  .q-marks {{ color: #666; font-size: 9.5pt; white-space: nowrap; margin-left: 6pt; flex-shrink: 0; }}
  /* Regular MCQ options: 2-column grid */
  .options {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 2pt 10pt;
    margin: 2pt 0 6pt 38pt;
    font-size: 10.5pt;
  }}
  .opt {{ display: block; }}
  /* Assertion-Reason options: single column */
  .ar-options {{
    margin: 4pt 0 6pt 38pt;
    font-size: 10pt;
  }}
  .ar-opt {{ margin-bottom: 2pt; }}
  .fig-note {{
    font-size: 9pt; color: #888; font-style: italic;
    margin: 2pt 0 4pt 38pt;
  }}
  .answer-space {{
    margin: 4pt 0 4pt 38pt;
    border-bottom: 1px dotted #bbb;
  }}
  /* ── Answer key ── */
  .page-break {{ page-break-before: always; }}
  .ak-title {{ font-size: 14pt; font-weight: bold; text-align: center; margin-bottom: 10pt; }}
  /* MCQ quick grid */
  .ak-mcq-title {{
    font-size: 11pt; font-weight: bold;
    margin: 10pt 0 4pt 0;
    padding-bottom: 2pt;
    border-bottom: 1px solid #aaa;
  }}
  .ak-mcq {{ width: 100%; border-collapse: collapse; font-size: 10pt; margin-bottom: 12pt; }}
  .ak-mcq td {{ border: 1px solid #ddd; padding: 3pt 6pt; }}
  .ak-letter {{ font-weight: bold; color: #1a1a8c; }}
  /* Detailed answer blocks */
  .ak-detail-title {{
    font-size: 11pt; font-weight: bold;
    margin: 8pt 0 4pt 0;
    padding-bottom: 2pt;
    border-bottom: 1px solid #aaa;
  }}
  .ak-block {{
    margin-bottom: 8pt;
    padding-bottom: 8pt;
    border-bottom: 1px dotted #ccc;
    page-break-inside: avoid;
  }}
  .ak-q-header {{ font-weight: bold; font-size: 10.5pt; margin-bottom: 2pt; }}
  .ak-q-answer {{ padding-left: 12pt; font-size: 10pt; line-height: 1.5; }}
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
  (3) Assertion-Reason questions: select the correct option from (A)–(D).
  (4) Read all questions carefully before answering.
  (5) Write answers clearly in the space provided.
</div>

{q_body}

<!-- ═══════════════════════ ANSWER KEY ═══════════════════════ -->
<div class='page-break'></div>
<div class='ak-title'>Answer Key — {_html_escape(paper.title)}</div>
<div class='meta-row'>{_html_escape(header_sub)} &nbsp;|&nbsp; Total Marks: {paper.total_marks} &nbsp;|&nbsp; Date: {today}</div>
<hr class='divider'>

{ak_mcq}
{ak_detail}

</body>
</html>"""

    return html


def generate_pdf(html: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=html).write_pdf()
