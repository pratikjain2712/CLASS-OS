"""
Seed 1,705 CBSE Class 9 Mathematics questions into ClassOS.

Questions from the Vizion platform extraction. MathML stripped; plain Unicode text.
Reads backend/data/cbse_class9_math_clean.json (committed alongside this script).

Usage (on EC2):
  docker compose -f docker-compose.prod.yml exec api python scripts/seed_cbse_class9_math.py
  -- or locally --
  DATABASE_URL=postgresql+asyncpg://classos:classos@localhost:5432/classos python scripts/seed_cbse_class9_math.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://classos:classos@db:5432/classos"
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "cbse_class9_math_clean.json")

CHAPTER_NAMES = [
    (1,  "Number Systems"),
    (2,  "Polynomials"),
    (3,  "Coordinate Geometry"),
    (4,  "Linear Equations in Two Variables"),
    (5,  "Introduction to Euclid's Geometry"),
    (6,  "Lines and Angles"),
    (7,  "Triangles"),
    (8,  "Quadrilaterals"),
    (9,  "Circles"),
    (10, "Heron's Formula"),
    (11, "Surface Areas and Volumes"),
    (12, "Statistics"),
    (13, "Probability"),
    (14, "Constructions"),
]


async def seed():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select, func

    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    with open(DATA_FILE, encoding="utf-8") as f:
        questions_data = json.load(f)

    async with Session() as db:
        from app.models.content import Publisher, Book, Chapter
        from app.models.questions import Question

        # Find or create publisher
        pub_res = await db.execute(select(Publisher).where(Publisher.name == "Arihant"))
        pub = pub_res.scalar_one_or_none()
        if not pub:
            pub = Publisher(name="Arihant")
            db.add(pub)
            await db.flush()
            print("Created publisher: Arihant")
        else:
            print(f"Using existing publisher: Arihant (id={pub.id})")

        # Find or create book
        book_res = await db.execute(
            select(Book).where(
                Book.publisher_id == pub.id,
                Book.title == "Arihant Mathematics Class 9",
                Book.class_ == 9,
                Book.board == "CBSE",
            )
        )
        book = book_res.scalar_one_or_none()
        if not book:
            book = Book(
                publisher_id=pub.id,
                title="Arihant Mathematics Class 9",
                subject="Mathematics",
                class_=9,
                board="CBSE",
                edition="2025-26",
            )
            db.add(book)
            await db.flush()
            print("Created book: Arihant Mathematics Class 9")
        else:
            print(f"Using existing book: {book.title} (id={book.id})")

        # Find or create all 14 chapters
        chapter_map: dict[int, Chapter] = {}
        for ch_num, ch_name in CHAPTER_NAMES:
            ch_res = await db.execute(
                select(Chapter).where(Chapter.book_id == book.id, Chapter.chapter_number == ch_num)
            )
            ch = ch_res.scalar_one_or_none()
            if not ch:
                ch = Chapter(
                    book_id=book.id,
                    chapter_number=ch_num,
                    chapter_name=ch_name,
                    processing_status="done",
                )
                db.add(ch)
                print(f"  Created chapter {ch_num}: {ch_name}")
            chapter_map[ch_num] = ch
        await db.flush()

        # Count existing questions to detect duplicates efficiently
        existing_count_res = await db.execute(
            select(func.count(Question.id)).where(
                Question.book_id == book.id,
                Question.board == "CBSE",
                Question.class_ == 9,
            )
        )
        existing_count = existing_count_res.scalar() or 0
        print(f"Existing CBSE Class 9 questions in DB: {existing_count}")

        # Build set of existing question prefixes (first 180 chars) for dedup
        existing_res = await db.execute(
            select(Question.question_text).where(
                Question.book_id == book.id,
                Question.board == "CBSE",
                Question.class_ == 9,
            )
        )
        existing_prefixes = {row[0][:180] for row in existing_res.all()}

        inserted = 0
        skipped = 0
        for i, q in enumerate(questions_data):
            prefix = q["question_text"][:180]
            if prefix in existing_prefixes:
                skipped += 1
                continue

            ch = chapter_map.get(q["chapter_number"])
            if not ch:
                skipped += 1
                continue

            q_obj = Question(
                source_type="publisher_bank",
                publisher_id=pub.id,
                book_id=book.id,
                chapter_id=ch.id,
                subject="Mathematics",
                class_=9,
                board="CBSE",
                question_type=q["q_type"],
                marks=q["marks"],
                difficulty=q["difficulty"],
                cognitive_level="Understanding",
                language="en",
                question_text=q["question_text"],
                options=None,
                answer=q["answer"],
                is_approved=True,
            )
            db.add(q_obj)
            existing_prefixes.add(prefix)
            inserted += 1

            if inserted % 200 == 0:
                await db.flush()
                print(f"  {inserted} inserted so far…")

        await db.commit()
        print(f"\nDone. Inserted: {inserted}, Skipped (duplicate): {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
