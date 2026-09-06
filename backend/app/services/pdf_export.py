"""
Generate a question paper PDF (question paper + answer key) using WeasyPrint.
"""

from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.papers import Paper, PaperQuestion


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _option_rows(options: list[dict]) -> str:
    items = "".join(
        f"<span class='opt'>({o['key']})&nbsp;{_html_escape(str(o['text']))}</span>"
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
        q_type = first_pq.question.question_type
        mpc = first_pq.marks
        count = len(pqs)
        sec_marks = mpc * count

        q_body += f"""
        <div class='section-header'>
            Section {sec_label} — {q_type} &nbsp;
            <span class='sec-meta'>({count} questions × {mpc} marks = {sec_marks} marks)</span>
        </div>"""

        for pq in pqs:
            q = pq.question
            q_body += f"""
            <div class='question'>
                <span class='q-num'>Q{q_global}.</span>
                <span class='q-text'>{_html_escape(q.question_text)}</span>
                <span class='q-marks'>[{pq.marks}M]</span>
            </div>"""
            if q.question_type == "MCQ" and q.options:
                q_body += _option_rows(q.options)
            # answer space lines for non-MCQ
            if q.question_type not in ("MCQ",):
                lines = max(2, pq.marks * 2)
                q_body += f"<div class='answer-space' style='height:{lines * 18}px'></div>"
            q_global += 1

    # ── Answer key body ────────────────────────────────────────────────────────
    ak_body = "<table class='ak-table'><thead><tr><th>Q#</th><th>Section</th><th>Type</th><th>Marks</th><th>Answer</th></tr></thead><tbody>"
    q_num = 1
    for sec_label, pqs in sections.items():
        for pq in pqs:
            q = pq.question
            answer_text = _html_escape(str(q.answer or ""))
            ak_body += f"<tr><td>{q_num}</td><td>{sec_label}</td><td>{q.question_type}</td><td>{pq.marks}</td><td class='ak-ans'>{answer_text}</td></tr>"
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
    margin: 2pt 0 2pt 28pt;
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
