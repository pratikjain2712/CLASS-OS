"""
Seed 40 SSC Maharashtra Board Class 8 Maths questions (Rational Numbers)
from pre-parsed Vizn data into ClassOS.

All Vizn HTML/MathML has been stripped; questions are plain Unicode text.

Usage (on EC2):
  docker compose -f docker-compose.prod.yml exec api python scripts/seed_vizn_questions.py
  -- or locally --
  DATABASE_URL=postgresql+asyncpg://classos:classos@localhost:5432/classos python scripts/seed_vizn_questions.py
"""

import asyncio
import os
import sys

# Ensure the app package is importable regardless of working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://classos:classos@db:5432/classos"
)

# ── Pre-parsed question data ──────────────────────────────────────────────────
# 40 questions: SSC Maharashtra Board, Class 8, Mathematics, Chapter: Rational Numbers
# All HTML/MathML stripped; difficulty derived from marks (<=2→Easy, 3→Medium, 4→Hard)

VIZN_QUESTIONS = [
    # VSA 1M — Compare rational numbers (13 questions)
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-7, -2',
     'options': None,
     'answer': '7 > 2\n∴ -7 < -2'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n0 , -9/5',
     'options': None,
     'answer': '0 > -9/5\nOn number line negative numbers are to the left of zero.'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n8/7 , 0',
     'options': None,
     'answer': '8/7 > 0\nOn the number line positive numbers are to the right of zero.'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-5/4, 1/4',
     'options': None,
     'answer': '-5/4 < 1/4\nNegative numbers are always less than positive numbers.'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n40/29, 141/29',
     'options': None,
     'answer': '40 < 141\n∴ 40/29 < 141/29'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-17/20, -13/20',
     'options': None,
     'answer': '∴ -17 < -13\n∴ -17/20 < -13/20'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers: -9 and -6',
     'options': None,
     'answer': '9 > 6\n∴ -9 < -6'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n7/25 , 17/25',
     'options': None,
     'answer': '7 < 17\n∴ 7/25 < 17/25'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n0, 5/8',
     'options': None,
     'answer': 'Zero is to the left of positive numbers.\n5/8 > 0'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-3, 0',
     'options': None,
     'answer': 'Zero is to the right of negative numbers.\n0 > -3'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n105/66 , 78/66',
     'options': None,
     'answer': '105 > 78\n∴ 105/66 > 78/66'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-17/9, -2/3',
     'options': None,
     'answer': 'LCM of 9 and 3 is 9.\n-17/9 × 1/1 = -17/9, -2/3 × 3/3 = -6/9\n17 > 6\n∴ -17 < -6\n∴ -17/9 < -2/3'},
    {'q_type': 'VSA', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-6/11 and 5/-8',
     'options': None,
     'answer': 'LCM of 11 and 8 is 88.\n-6/11 = -48/88\n5/-8 = -55/88\n55 > 48\n∴ -55 < -48\n∴ -5/8 < -6/11 or -6/11 > 5/-8'},

    # SA 2M — Compare with LCM (4 questions)
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n15/12, 7/16',
     'options': None,
     'answer': 'LCM of 12 and 16 is 48\n15×4/12×4 = 60/48\n7×3/16×3 = 21/48\n60/48 > 21/48\n∴ 15/12 > 7/16'},
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-25/8, -9/4',
     'options': None,
     'answer': 'LCM is 8\n-9×2/4×2 = -18/8\n-25 < -18\n∴ -25/8 < -18/8'},
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n12/15, 3/5',
     'options': None,
     'answer': 'LCM is 15\n3×3/5×3 = 9/15\n12/15 > 9/15'},
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Compare the following numbers.\n-7/11, -3/4',
     'options': None,
     'answer': 'LCM is 44\n-7×4/11×4 = -28/44\n-3×11/4×11 = -33/44\n-28 > -33\n∴ -7/11 > -3/4'},

    # SA 2M — Represent on number line (3 questions)
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Represent 3/4 on the number line.',
     'options': None,
     'answer': 'See solution'},
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Represent 7/3 and -7/3 on the number line.\n7/3 = 21/3, -7/3 = -21/3',
     'options': None,
     'answer': 'See solution'},
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Represent 3/5 and -8/5 on the number line.\n-8/5 = -13/5',
     'options': None,
     'answer': 'See solution'},

    # SA 2M — Decimal form (3 questions)
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Write the following rational numbers in decimal form.\n6/21',
     'options': None,
     'answer': '6÷3 / 21÷3 = 2/7'},
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Write the following rational numbers in decimal form.\n17/9',
     'options': None,
     'answer': 'See solution'},
    {'q_type': 'SA', 'marks': 2, 'difficulty': 'Easy',
     'question_text': 'Write the following rational numbers in decimal form.\n27/4',
     'options': None,
     'answer': 'See solution'},

    # SA 3M — Show on number line (5 questions)
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Show the following numbers on a number line. Draw a separate number line for each example.\n3/2, 5/2, -3/2',
     'options': None,
     'answer': 'See solution'},
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Show the following numbers on a number line. Draw a separate number line for each example.\n7/5, -2/5, -4/5',
     'options': None,
     'answer': 'See solution'},
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Show the following numbers on a number line. Draw a separate number line for each example.\n-5/8, 11/8',
     'options': None,
     'answer': 'See solution'},
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Show the following numbers on a number line. Draw a separate number line for each example.\n13/10, -17/10',
     'options': None,
     'answer': 'See solution'},
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': (
         'Observe the number line and answer the questions.\n\n'
         'i. Which number is indicated by point B?\n\n'
         'ii. Which point indicates the number 1 3/4?\n\n'
         "iii. State whether the statement 'the point D denotes the number 5/2' is true or false."
     ),
     'options': None,
     'answer': (
         'i. -2 1/2\n\n'
         'ii. 1×4+3/4 = 4+3/4 = 7/4\n∴ The number 1 3/4 is indicated by point C\n\n'
         "iii. State whether the statement 'the point D denotes the number 5/2' is true."
     )},

    # SA 3M — Decimal form (4 questions)
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Write the following rational numbers in decimal form.\n9/37',
     'options': None,
     'answer': '9/37 = 0.243'},
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Write the following rational numbers in decimal form.\n18/42',
     'options': None,
     'answer': '18÷6 / 42÷6 = 3/7\n∴ 3/7 or 18/42 = 0.428571...'},
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Write the following rational numbers in decimal form.\n9/14',
     'options': None,
     'answer': '∴ 9/14 = 0.6428571...'},
    {'q_type': 'SA', 'marks': 3, 'difficulty': 'Medium',
     'question_text': 'Write the following rational numbers in decimal form.\n-103/5',
     'options': None,
     'answer': '-103/5 = -20.6'},

    # LA 4M — Irrational numbers on number line (2 questions)
    {'q_type': 'LA', 'marks': 4, 'difficulty': 'Hard',
     'question_text': (
         'The number √2 is shown on a number line. Steps are given to show √3 on the number line '
         'using √2. Fill in the boxes properly and complete the activity.\n\n'
         'The point Q on the number line shows the number √2.\n'
         'A line perpendicular to the number line is drawn through the point. R is at unit distance from Q on the line.\n'
         'Right angled △ is obtained by drawing seg OR.\n'
         'l(OQ) = √2, l(QR) = 1\n\n'
         '[l(OR)]² = [l(OQ)]² + [l(QR)]²\n'
         '= ___ + ___\n'
         '= ___ + ___\n'
         '= ___\n'
         '[l(OR)]² = ___'
     ),
     'options': None,
     'answer': (
         'The point Q on the number line shows the number √2.\n'
         'A line perpendicular to the number line is drawn through the point Q. R is at unit distance from Q on the line.\n'
         'Right angled △OPQ is obtained by drawing seg OR.\n'
         'l(OQ) = √2, l(QR) = 1\n\n'
         '[l(OR)]² = [l(OQ)]² + [l(QR)]²\n'
         '= (√2)² + (1)²\n'
         '= 2 + 1\n'
         '= 3\n'
         '∴ [l(OR)] = √3'
     )},
    {'q_type': 'LA', 'marks': 4, 'difficulty': 'Hard',
     'question_text': 'Show the number √5 on the number line.',
     'options': None,
     'answer': (
         'On point Q on the number line shows the number 2. Draw QR of length = 1 perpendicular to the number line.\n'
         'Join segment OR.\n'
         'In △ORQ, by Pythagoras theorem:\n'
         '[l(OR)]² = [l(OQ)]² + [l(QR)]²\n'
         '= (2)² + (1)²\n'
         '= 4 + 1 = 5\n'
         '∴ l(OR) = √5\n\n'
         'Draw an arc with centre O and radius OR. Mark the point of intersection of line and arc as C.\n'
         'Point C denotes √5.'
     )},

    # MCQ 1M — Rational number properties (6 questions)
    {'q_type': 'MCQ', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'If m and n both are positive numbers then m/n is ___ rational number.',
     'options': [
         {'key': 'A', 'text': 'Positive'},
         {'key': 'B', 'text': 'Negative'},
         {'key': 'C', 'text': 'Both a and b'},
         {'key': 'D', 'text': 'None of these'},
     ],
     'answer': 'A'},
    {'q_type': 'MCQ', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'If a/b and c/d are rational numbers such that b and d are positive and a × d = b × c, then:',
     'options': [
         {'key': 'A', 'text': 'a/b < c/d'},
         {'key': 'B', 'text': 'a/b = c/d'},
         {'key': 'C', 'text': 'a/b > c/d'},
         {'key': 'D', 'text': 'All of the above'},
     ],
     'answer': 'B'},
    {'q_type': 'MCQ', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'If a < b then -a > -b.',
     'options': [
         {'key': 'A', 'text': 'True'},
         {'key': 'B', 'text': 'False'},
     ],
     'answer': 'A'},
    {'q_type': 'MCQ', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'When a number is divided by another number and the remainder is zero, the decimal expansion is terminating.',
     'options': [
         {'key': 'A', 'text': 'True'},
         {'key': 'B', 'text': 'False'},
     ],
     'answer': 'A'},
    {'q_type': 'MCQ', 'marks': 1, 'difficulty': 'Easy',
     'question_text': '23/99 is ___',
     'options': [
         {'key': 'A', 'text': '0.2323...'},
         {'key': 'B', 'text': 'Non terminating recurring.'},
         {'key': 'C', 'text': '0.23'},
         {'key': 'D', 'text': 'All of these.'},
     ],
     'answer': 'D'},
    {'q_type': 'MCQ', 'marks': 1, 'difficulty': 'Easy',
     'question_text': 'π is a rational number.',
     'options': [
         {'key': 'A', 'text': 'True'},
         {'key': 'B', 'text': 'False'},
     ],
     'answer': 'B'},
]


# ── Main seed ─────────────────────────────────────────────────────────────────

async def seed():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select

    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        from app.models.institute import Institute
        from app.models.content import Publisher, Book, Chapter
        from app.models.questions import Question

        inst_r = await db.execute(select(Institute).where(Institute.name == "Arihant Educare"))
        if not inst_r.scalar_one_or_none():
            print("ERROR: Run seed_demo.py first (Arihant Educare institute must exist).")
            sys.exit(1)

        dup_r = await db.execute(
            select(Question).where(
                Question.board == "Maharashtra SSC",
                Question.class_ == 8,
            ).limit(1)
        )
        if dup_r.scalar_one_or_none():
            print("SSC Class 8 questions already seeded — skipping.")
            return

        pub_r = await db.execute(select(Publisher).where(Publisher.name == "SSC Maharashtra Board"))
        pub = pub_r.scalar_one_or_none()
        if not pub:
            pub = Publisher(name="SSC Maharashtra Board")
            db.add(pub)
            await db.flush()

        book_r = await db.execute(select(Book).where(Book.title == "SSC Mathematics Class 8"))
        book = book_r.scalar_one_or_none()
        if not book:
            book = Book(
                publisher_id=pub.id,
                title="SSC Mathematics Class 8",
                subject="Mathematics",
                class_=8,
                board="Maharashtra SSC",
                edition="2025-26",
            )
            db.add(book)
            await db.flush()

        chap_r = await db.execute(
            select(Chapter).where(
                Chapter.book_id == book.id,
                Chapter.chapter_name == "Rational Numbers",
            )
        )
        chapter = chap_r.scalar_one_or_none()
        if not chapter:
            chapter = Chapter(
                book_id=book.id,
                chapter_number=1,
                chapter_name="Rational Numbers",
                processing_status="done",
            )
            db.add(chapter)
            await db.flush()

        count = 0
        for q in VIZN_QUESTIONS:
            q_obj = Question(
                source_type="publisher_bank",
                publisher_id=pub.id,
                book_id=book.id,
                chapter_id=chapter.id,
                subject="Mathematics",
                class_=8,
                board="Maharashtra SSC",
                question_type=q["q_type"],
                marks=q["marks"],
                difficulty=q["difficulty"],
                cognitive_level="Understanding",
                language="en",
                question_text=q["question_text"],
                options=q["options"],
                answer=q["answer"],
            )
            db.add(q_obj)
            count += 1
            print(f"  + [{q['q_type']} {q['marks']}M {q['difficulty']}] {q['question_text'][:70]}")

        await db.commit()
        print(f"\n✓ Seeded {count} questions")


if __name__ == "__main__":
    asyncio.run(seed())
