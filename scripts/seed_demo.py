"""
Seed a demo institute + teacher + sample questions for local testing.

Usage:
  DATABASE_URL=postgresql+asyncpg://... python scripts/seed_demo.py
"""

import asyncio
import os
import uuid
from passlib.context import CryptContext

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/classos"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select

    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        from app.models.institute import Institute, Branch, User
        from app.models.content import Publisher, Book, Chapter
        from app.models.questions import Question
        from app.models.credits import InstituteCredits

        # Skip if already seeded
        existing = await db.execute(select(User).where(User.email == "admin@classos.io"))
        if existing.scalar_one_or_none():
            print("Demo data already seeded — skipping.")
            return

        # Institute
        inst = Institute(name="Arihant Educare", subscription_plan="pro")
        db.add(inst)
        await db.flush()

        # Branch
        branch = Branch(institute_id=inst.id, name="Arihant Educare — Pune", city="Pune")
        db.add(branch)
        await db.flush()

        # Credits
        credits = InstituteCredits(institute_id=inst.id, current_balance=100, total_purchased=100)
        db.add(credits)

        # Platform admin
        admin = User(
            institute_id=inst.id,
            role="platform_admin",
            name="ClassOS Admin",
            email="admin@classos.io",
            password_hash=pwd_context.hash("admin123"),
        )
        db.add(admin)

        # Teacher
        teacher = User(
            institute_id=inst.id,
            branch_id=branch.id,
            role="teacher",
            name="Priya Kulkarni",
            email="priya@arihant.edu",
            password_hash=pwd_context.hash("teacher123"),
        )
        db.add(teacher)
        await db.flush()

        # Get Arihant publisher
        pub_result = await db.execute(select(Publisher).where(Publisher.name == "Arihant"))
        pub = pub_result.scalar_one_or_none()
        if not pub:
            pub = Publisher(name="Arihant")
            db.add(pub)
            await db.flush()

        # Book
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

        # Chapters
        chapter_data = [
            (1, "Number Systems"),
            (2, "Polynomials"),
            (3, "Coordinate Geometry"),
            (4, "Linear Equations in Two Variables"),
            (5, "Introduction to Euclid's Geometry"),
            (6, "Lines and Angles"),
            (7, "Triangles"),
            (8, "Quadrilaterals"),
        ]
        chapters = []
        for num, name in chapter_data:
            ch = Chapter(
                book_id=book.id,
                chapter_number=num,
                chapter_name=name,
                processing_status="done",
            )
            db.add(ch)
            chapters.append(ch)
        await db.flush()

        # Sample questions for Chapter 2 (Polynomials) and Chapter 6 (Lines and Angles)
        sample_qs = [
            # Chapter 2 — Polynomials
            {
                "chapter": chapters[1],
                "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
                "question_text": "The degree of the polynomial 4x³ + 3x² − 2x + 5 is:",
                "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}, {"key": "C", "text": "3"}, {"key": "D", "text": "4"}],
                "answer": "C",
                "solution": "The degree is the highest power of the variable, which is 3.",
                "cognitive_level": "Knowledge",
            },
            {
                "chapter": chapters[1],
                "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
                "question_text": "Which of the following is a zero of the polynomial p(x) = x² − 5x + 6?",
                "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}, {"key": "C", "text": "4"}, {"key": "D", "text": "5"}],
                "answer": "B",
                "solution": "p(2) = 4 − 10 + 6 = 0. So x = 2 is a zero.",
                "cognitive_level": "Understanding",
            },
            {
                "chapter": chapters[1],
                "question_type": "VSA", "marks": 2, "difficulty": "Easy",
                "question_text": "Find the value of the polynomial p(y) = y² − y + 1 at y = 1.",
                "options": None,
                "answer": "p(1) = 1 − 1 + 1 = 1",
                "solution": "Substitute y = 1: p(1) = (1)² − 1 + 1 = 1.",
                "cognitive_level": "Knowledge",
            },
            {
                "chapter": chapters[1],
                "question_type": "SA", "marks": 4, "difficulty": "Medium",
                "question_text": "Using the factor theorem, show that (x − 2) is a factor of x³ − 6x² + 11x − 6. Hence factorise the polynomial completely.",
                "options": None,
                "answer": "(x − 1)(x − 2)(x − 3)",
                "solution": "p(2) = 8 − 24 + 22 − 6 = 0. So (x−2) is a factor. Dividing: x³−6x²+11x−6 = (x−2)(x²−4x+3) = (x−2)(x−1)(x−3).",
                "cognitive_level": "Application",
            },
            {
                "chapter": chapters[1],
                "question_type": "LA", "marks": 5, "difficulty": "Hard",
                "question_text": "State and prove the Remainder Theorem. Hence find the remainder when p(x) = 2x³ − 3x² + 4x − 1 is divided by (x − 2).",
                "options": None,
                "answer": "Remainder = 11",
                "solution": "Remainder Theorem: If p(x) is divided by (x−a), the remainder is p(a). p(2) = 2(8) − 3(4) + 4(2) − 1 = 16 − 12 + 8 − 1 = 11.",
                "cognitive_level": "Analysis",
            },
            # Chapter 6 — Lines and Angles
            {
                "chapter": chapters[5],
                "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
                "question_text": "The supplement of an angle of 75° is:",
                "options": [{"key": "A", "text": "15°"}, {"key": "B", "text": "105°"}, {"key": "C", "text": "115°"}, {"key": "D", "text": "285°"}],
                "answer": "B",
                "solution": "Supplementary angles sum to 180°. 180° − 75° = 105°.",
                "cognitive_level": "Knowledge",
            },
            {
                "chapter": chapters[5],
                "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
                "question_text": "If two lines intersect each other, then the vertically opposite angles are:",
                "options": [{"key": "A", "text": "Supplementary"}, {"key": "B", "text": "Complementary"}, {"key": "C", "text": "Equal"}, {"key": "D", "text": "Adjacent"}],
                "answer": "C",
                "solution": "Vertically opposite angles are always equal (theorem).",
                "cognitive_level": "Understanding",
            },
            {
                "chapter": chapters[5],
                "question_type": "VSA", "marks": 2, "difficulty": "Easy",
                "question_text": "In a triangle, if two angles are 45° and 60°, find the third angle.",
                "options": None,
                "answer": "75°",
                "solution": "Angle sum = 180°. Third angle = 180° − 45° − 60° = 75°.",
                "cognitive_level": "Application",
            },
            {
                "chapter": chapters[5],
                "question_type": "SA", "marks": 4, "difficulty": "Medium",
                "question_text": "Prove that if a transversal intersects two parallel lines, then the pair of alternate interior angles is equal.",
                "options": None,
                "answer": "Alternate interior angles are equal — proved using the linear pair and vertically opposite angles properties.",
                "solution": "Let lines AB ∥ CD, with transversal PQ. ∠3 and ∠6 are alternate interior angles. Since AB ∥ CD, ∠2 = ∠6 (corresponding angles). Also ∠2 = ∠3 (vertically opposite). Therefore ∠3 = ∠6.",
                "cognitive_level": "Analysis",
            },
            {
                "chapter": chapters[5],
                "question_type": "MCQ", "marks": 1, "difficulty": "Hard",
                "question_text": "In the given figure, AB ∥ CD and a transversal EF intersects them at G and H. If ∠EGB = 50°, what is ∠GHD?",
                "options": [{"key": "A", "text": "50°"}, {"key": "B", "text": "130°"}, {"key": "C", "text": "140°"}, {"key": "D", "text": "80°"}],
                "answer": "B",
                "solution": "∠GHD and ∠EGB are co-interior (same-side interior) angles: they sum to 180°. So ∠GHD = 180° − 50° = 130°.",
                "cognitive_level": "Application",
            },
        ]

        for qd in sample_qs:
            ch = qd["chapter"]
            q = Question(
                source_type="publisher_bank",
                chapter_id=ch.id,
                book_id=book.id,
                publisher_id=pub.id,
                subject="Mathematics",
                class_=9,
                board="CBSE",
                question_type=qd["question_type"],
                marks=qd["marks"],
                difficulty=qd["difficulty"],
                question_text=qd["question_text"],
                options=qd["options"],
                answer=qd["answer"],
                solution=qd["solution"],
                cognitive_level=qd["cognitive_level"],
                is_approved=True,
            )
            db.add(q)

        await db.commit()
        print("✅ Demo data seeded successfully")
        print("   Login: priya@arihant.edu / teacher123")
        print("   Admin: admin@classos.io / admin123")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    asyncio.run(seed())
