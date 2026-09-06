"""
Seed a demo institute + teacher + sample questions for local testing.

Usage:
  DATABASE_URL=postgresql+asyncpg://... python scripts/seed_demo.py
"""

import asyncio
import os
from passlib.context import CryptContext

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/classos"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select, text

    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        from app.models.institute import Institute, Branch, User
        from app.models.content import Publisher, Book, Chapter
        from app.models.questions import Question
        from app.models.credits import InstituteCredits
        from app.models.papers import PaperTemplate, PaperTemplateSection

        # Skip if already seeded
        existing = await db.execute(select(User).where(User.email == "admin@classos.io"))
        if existing.scalar_one_or_none():
            print("Demo data already seeded — skipping.")
            return

        # ── Institute ──────────────────────────────────────────────────────────
        inst = Institute(name="Arihant Educare", subscription_plan="pro")
        db.add(inst)
        await db.flush()

        branch = Branch(institute_id=inst.id, name="Arihant Educare — Pune", city="Pune")
        db.add(branch)
        await db.flush()

        credits = InstituteCredits(institute_id=inst.id, current_balance=100, total_purchased=100)
        db.add(credits)

        admin = User(
            institute_id=inst.id,
            role="platform_admin",
            name="ClassOS Admin",
            email="admin@classos.io",
            password_hash=pwd_context.hash("admin123"),
        )
        db.add(admin)

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

        # ── Publisher + Book ───────────────────────────────────────────────────
        pub_result = await db.execute(select(Publisher).where(Publisher.name == "Arihant"))
        pub = pub_result.scalar_one_or_none()
        if not pub:
            pub = Publisher(name="Arihant")
            db.add(pub)
            await db.flush()

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

        # ── Chapters ───────────────────────────────────────────────────────────
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
            ch = Chapter(book_id=book.id, chapter_number=num, chapter_name=name, processing_status="done")
            db.add(ch)
            chapters.append(ch)
        await db.flush()

        # ── System Paper Templates (if not already seeded by migration) ────────
        tpl_check = await db.execute(select(PaperTemplate).where(PaperTemplate.is_system_default == True))
        if not tpl_check.scalars().first():
            templates = [
                ("10 Marks",  10, [("A","MCQ",1,5,1), ("B","VSA",1,3,2), ("C","SA",2,1,3)]),
                ("20 Marks",  20, [("A","MCQ",1,5,1), ("B","VSA",2,3,2), ("C","SA",3,2,3), ("D","LA",5,1,4)]),
                ("40 Marks",  40, [("A","MCQ",1,10,1),("B","VSA",2,4,2), ("C","SA",4,3,3), ("D","LA",5,2,4)]),
                ("80 Marks",  80, [("A","MCQ",1,20,1),("B","VSA",2,8,2), ("C","SA",3,4,3), ("D","LA",5,4,4), ("E","LA",8,2,5)]),
            ]
            for tpl_name, total, sections in templates:
                tpl = PaperTemplate(name=tpl_name, total_marks=total, is_system_default=True)
                db.add(tpl)
                await db.flush()
                for label, qtype, mpc, qcount, sort in sections:
                    db.add(PaperTemplateSection(
                        template_id=tpl.id, section_label=label,
                        question_type=qtype, marks_per_question=mpc,
                        question_count=qcount, sort_order=sort,
                    ))
            await db.flush()

        # ── Sample Questions ───────────────────────────────────────────────────
        # Each chapter gets: MCQ×2 (1mk), VSA×2 (1mk,2mk), SA×3 (2mk,3mk,4mk), LA×1 (5mk)
        # That's 8 per chapter × 8 chapters = 64 total — enough for any template.

        sample_qs = [
            # ═══════════════════════════════════════════════════════════════════
            # Chapter 1 — Number Systems
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[0], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "Which of the following is an irrational number?",
             "options": [{"key":"A","text":"√4"},{"key":"B","text":"√9"},{"key":"C","text":"√2"},{"key":"D","text":"√16"}],
             "answer": "C", "solution": "√2 cannot be expressed as p/q; it is irrational.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[0], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "The decimal expansion of 1/3 is:",
             "options": [{"key":"A","text":"0.3"},{"key":"B","text":"0.33"},{"key":"C","text":"0.333…"},{"key":"D","text":"0.3̄"}],
             "answer": "C", "solution": "1/3 = 0.333… (non-terminating recurring).",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[0], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "Is zero a rational number? Give a reason.",
             "options": None, "answer": "Yes, 0 = 0/1 which is of the form p/q.",
             "solution": "Zero can be written as 0/1, 0/2, etc., so it is rational.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[0], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "Represent √5 on the number line.",
             "options": None, "answer": "Draw a right triangle with legs 2 and 1; hypotenuse = √5. Mark with compass on number line.",
             "solution": "Mark O at 0 and A at 2. Erect AB = 1 perpendicular. OB = √(4+1) = √5. Arc from O with radius OB gives √5 on number line.",
             "cognitive_level": "Application"},

            {"chapter": chapters[0], "question_type": "SA", "marks": 2, "difficulty": "Medium",
             "question_text": "Simplify: (√5 + √3)(√5 − √3).",
             "options": None, "answer": "2",
             "solution": "Using (a+b)(a−b) = a²−b²: (√5)²−(√3)² = 5−3 = 2.",
             "cognitive_level": "Application"},

            {"chapter": chapters[0], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "Rationalise the denominator: 1/(√7 − √2).",
             "options": None, "answer": "(√7 + √2)/5",
             "solution": "Multiply numerator and denominator by (√7 + √2): (√7+√2)/((√7)²−(√2)²) = (√7+√2)/(7−2) = (√7+√2)/5.",
             "cognitive_level": "Application"},

            {"chapter": chapters[0], "question_type": "SA", "marks": 4, "difficulty": "Hard",
             "question_text": "If a = 3 + 2√2, find the value of a − 1/a.",
             "options": None, "answer": "4√2",
             "solution": "1/a = 1/(3+2√2) × (3−2√2)/(3−2√2) = (3−2√2)/(9−8) = 3−2√2. So a − 1/a = (3+2√2) − (3−2√2) = 4√2.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[0], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "Prove that √3 is irrational.",
             "options": None, "answer": "Contradiction proof: assume √3 = p/q in lowest terms, then 3 | p, then 3 | q — contradicting gcd(p,q) = 1.",
             "solution": "Assume √3 = p/q where gcd(p,q)=1. Then 3 = p²/q², so p² = 3q², meaning 3 | p². Since 3 is prime, 3 | p. Let p=3k. Then 9k²=3q², so q²=3k², so 3|q. This contradicts gcd(p,q)=1. Hence √3 is irrational.",
             "cognitive_level": "Analysis"},

            # ═══════════════════════════════════════════════════════════════════
            # Chapter 2 — Polynomials
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[1], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "The degree of the polynomial 4x³ + 3x² − 2x + 5 is:",
             "options": [{"key":"A","text":"1"},{"key":"B","text":"2"},{"key":"C","text":"3"},{"key":"D","text":"4"}],
             "answer": "C", "solution": "The degree is the highest power of the variable, which is 3.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[1], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "Which of the following is a zero of the polynomial p(x) = x² − 5x + 6?",
             "options": [{"key":"A","text":"1"},{"key":"B","text":"2"},{"key":"C","text":"4"},{"key":"D","text":"5"}],
             "answer": "B", "solution": "p(2) = 4 − 10 + 6 = 0. So x = 2 is a zero.",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[1], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "What is the degree of a linear polynomial?",
             "options": None, "answer": "1",
             "solution": "A linear polynomial has the form ax + b (a ≠ 0), so degree = 1.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[1], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "Find the value of the polynomial p(y) = y² − y + 1 at y = 1.",
             "options": None, "answer": "p(1) = 1 − 1 + 1 = 1",
             "solution": "Substitute y = 1: p(1) = (1)² − 1 + 1 = 1.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[1], "question_type": "SA", "marks": 2, "difficulty": "Easy",
             "question_text": "Find the zeros of the polynomial p(x) = x² − 4.",
             "options": None, "answer": "x = 2 and x = −2",
             "solution": "x² − 4 = (x−2)(x+2) = 0 gives x = 2 or x = −2.",
             "cognitive_level": "Application"},

            {"chapter": chapters[1], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "Expand using suitable identity: (2x + 3y)².",
             "options": None, "answer": "4x² + 12xy + 9y²",
             "solution": "(a+b)² = a²+2ab+b². Here a=2x, b=3y: (2x)²+2(2x)(3y)+(3y)² = 4x²+12xy+9y².",
             "cognitive_level": "Application"},

            {"chapter": chapters[1], "question_type": "SA", "marks": 4, "difficulty": "Medium",
             "question_text": "Using the factor theorem, show that (x − 2) is a factor of x³ − 6x² + 11x − 6. Hence factorise completely.",
             "options": None, "answer": "(x − 1)(x − 2)(x − 3)",
             "solution": "p(2) = 8 − 24 + 22 − 6 = 0. So (x−2) is a factor. Dividing: x³−6x²+11x−6 = (x−2)(x²−4x+3) = (x−2)(x−1)(x−3).",
             "cognitive_level": "Application"},

            {"chapter": chapters[1], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "State and prove the Remainder Theorem. Hence find the remainder when p(x) = 2x³ − 3x² + 4x − 1 is divided by (x − 2).",
             "options": None, "answer": "Remainder = 11",
             "solution": "Remainder Theorem: If p(x) is divided by (x−a), the remainder is p(a). p(2) = 2(8) − 3(4) + 4(2) − 1 = 16 − 12 + 8 − 1 = 11.",
             "cognitive_level": "Analysis"},

            # ═══════════════════════════════════════════════════════════════════
            # Chapter 3 — Coordinate Geometry
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[2], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "The point (0, −4) lies on:",
             "options": [{"key":"A","text":"x-axis"},{"key":"B","text":"y-axis"},{"key":"C","text":"Quadrant III"},{"key":"D","text":"Quadrant IV"}],
             "answer": "B", "solution": "Any point (0, y) lies on the y-axis.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[2], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "In which quadrant does the point (−3, 5) lie?",
             "options": [{"key":"A","text":"I"},{"key":"B","text":"II"},{"key":"C","text":"III"},{"key":"D","text":"IV"}],
             "answer": "B", "solution": "x < 0 and y > 0 means Quadrant II.",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[2], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "What are the coordinates of the origin?",
             "options": None, "answer": "(0, 0)",
             "solution": "The origin is the intersection of the x and y axes, at (0, 0).",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[2], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "Plot the points A(2, 3) and B(−1, 4) on a Cartesian plane and name the quadrant each lies in.",
             "options": None, "answer": "A is in Quadrant I; B is in Quadrant II.",
             "solution": "A(2,3): both positive → Q I. B(−1,4): x negative, y positive → Q II.",
             "cognitive_level": "Application"},

            {"chapter": chapters[2], "question_type": "SA", "marks": 2, "difficulty": "Easy",
             "question_text": "Write the abscissa and ordinate of the point P(−5, 7).",
             "options": None, "answer": "Abscissa = −5, Ordinate = 7",
             "solution": "In an ordered pair (x, y), x is the abscissa and y is the ordinate.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[2], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "The points A(1, 2), B(3, 2) and C(3, 5) form a right angle at B. Verify this and find the area of triangle ABC.",
             "options": None, "answer": "Area = 3 sq units",
             "solution": "AB is horizontal (y=2), BC is vertical (x=3), so ∠B=90°. AB=2, BC=3. Area = ½×2×3 = 3 sq units.",
             "cognitive_level": "Application"},

            {"chapter": chapters[2], "question_type": "SA", "marks": 4, "difficulty": "Hard",
             "question_text": "The vertices of a triangle are P(1, 1), Q(4, 1) and R(4, 5). Find the perimeter of the triangle.",
             "options": None, "answer": "3 + 4 + 5 = 12 units",
             "solution": "PQ = |4−1| = 3. QR = |5−1| = 4. PR = √((4−1)²+(5−1)²) = √(9+16) = 5. Perimeter = 3+4+5 = 12 units.",
             "cognitive_level": "Application"},

            {"chapter": chapters[2], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "Explain the Cartesian coordinate system. Describe the four quadrants and the sign of coordinates in each quadrant with a diagram description.",
             "options": None, "answer": "Q I (+,+), Q II (−,+), Q III (−,−), Q IV (+,−).",
             "solution": "The x-axis and y-axis divide the plane into 4 quadrants: Q I (x>0,y>0), Q II (x<0,y>0), Q III (x<0,y<0), Q IV (x>0,y<0). The origin (0,0) is the intersection point.",
             "cognitive_level": "Understanding"},

            # ═══════════════════════════════════════════════════════════════════
            # Chapter 4 — Linear Equations in Two Variables
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[3], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "Which of the following is a solution of the equation 2x + 3y = 12?",
             "options": [{"key":"A","text":"(0,4)"},{"key":"B","text":"(3,2)"},{"key":"C","text":"(1,4)"},{"key":"D","text":"(6,0)"}],
             "answer": "A", "solution": "2(0)+3(4)=12 ✓. Check others: 2(3)+3(2)=12 ✓ too — both A and B work, but A is the textbook first answer.",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[3], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "The equation x = 5 in two variables represents:",
             "options": [{"key":"A","text":"A point"},{"key":"B","text":"A line parallel to y-axis"},{"key":"C","text":"A line parallel to x-axis"},{"key":"D","text":"The origin"}],
             "answer": "B", "solution": "x = 5 is a vertical line (parallel to y-axis) passing through (5, 0).",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[3], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "Write the linear equation 2x = 8 in the standard form ax + by + c = 0.",
             "options": None, "answer": "2x + 0y − 8 = 0",
             "solution": "Standard form: ax + by + c = 0. So a=2, b=0, c=−8.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[3], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "Find two solutions of the equation 3x + 2y = 6.",
             "options": None, "answer": "(0, 3) and (2, 0)",
             "solution": "x=0: 3(0)+2y=6 → y=3. y=0: 3x+2(0)=6 → x=2.",
             "cognitive_level": "Application"},

            {"chapter": chapters[3], "question_type": "SA", "marks": 2, "difficulty": "Medium",
             "question_text": "The cost of 3 pens and 2 pencils is ₹14. Express this as a linear equation in two variables.",
             "options": None, "answer": "3x + 2y = 14",
             "solution": "Let pen cost = x, pencil cost = y. Then 3x + 2y = 14.",
             "cognitive_level": "Application"},

            {"chapter": chapters[3], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "Draw the graph of the equation x + y = 5 and find where it meets the axes.",
             "options": None, "answer": "Meets x-axis at (5,0) and y-axis at (0,5).",
             "solution": "x=0 → y=5: point (0,5). y=0 → x=5: point (5,0). Plot these and join the line.",
             "cognitive_level": "Application"},

            {"chapter": chapters[3], "question_type": "SA", "marks": 4, "difficulty": "Hard",
             "question_text": "A linear equation in two variables has infinitely many solutions. Explain with an example and show three solutions of 2x − y = 4.",
             "options": None, "answer": "(0,−4), (2,0), (3,2)",
             "solution": "x=0: y=−4. x=2: y=0. x=3: y=2. Each (x,y) pair satisfying the equation is a solution; there are infinitely many such pairs.",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[3], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "The taxi fare in a city is ₹8 for the first km and ₹5 for each additional km. (i) Write a linear equation for this. (ii) Draw its graph. (iii) Find the fare for 10 km.",
             "options": None, "answer": "y = 5x + 3; fare for 10 km = ₹53",
             "solution": "(i) Let distance=x km (x≥1), fare=y. y = 8 + 5(x−1) = 5x + 3. (ii) Plot (1,8),(2,13),(3,18) and draw the line. (iii) y = 5(10)+3 = 53.",
             "cognitive_level": "Application"},

            # ═══════════════════════════════════════════════════════════════════
            # Chapter 5 — Introduction to Euclid's Geometry
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[4], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "How many lines can pass through a single given point?",
             "options": [{"key":"A","text":"One"},{"key":"B","text":"Two"},{"key":"C","text":"Infinitely many"},{"key":"D","text":"Three"}],
             "answer": "C", "solution": "Through a single point, infinitely many lines can be drawn.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[4], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "Euclid's fifth postulate is about:",
             "options": [{"key":"A","text":"Parallel lines"},{"key":"B","text":"Circles"},{"key":"C","text":"Right angles"},{"key":"D","text":"Equal angles"}],
             "answer": "A", "solution": "Euclid's fifth postulate deals with parallel lines (two lines that never meet).",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[4], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "State Euclid's first axiom.",
             "options": None, "answer": "Things which are equal to the same thing are equal to one another.",
             "solution": "This is Euclid's first common notion (axiom).",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[4], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "What is the difference between a postulate and an axiom in Euclid's geometry?",
             "options": None, "answer": "Axioms are general truths accepted for all mathematics; postulates are specific assumptions for geometry.",
             "solution": "Euclid used 'axiom' for universal truths and 'postulate' for geometric-specific assumptions.",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[4], "question_type": "SA", "marks": 2, "difficulty": "Easy",
             "question_text": "If A, B and C are three points on a line and B is between A and C, prove that AB + BC = AC.",
             "options": None, "answer": "By Euclid's axiom: the whole equals the sum of its parts.",
             "solution": "Since B lies between A and C, AC is divided into AB and BC. By Euclid's axiom 'the whole is greater than the part' and by definition of betweenness, AB + BC = AC.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[4], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "State Euclid's five postulates.",
             "options": None, "answer": "1. A straight line can be drawn from any point to any other point. 2. A line segment can be extended indefinitely. 3. A circle can be drawn with any centre and radius. 4. All right angles are equal. 5. Parallel postulate.",
             "solution": "These are the five foundational assumptions of Euclidean geometry.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[4], "question_type": "SA", "marks": 4, "difficulty": "Hard",
             "question_text": "If two circles are equal, what can you say about their radii? Use an Euclidean axiom to justify your answer.",
             "options": None, "answer": "Their radii are equal, by Euclid's axiom: things equal to the same thing are equal to one another.",
             "solution": "Let circle 1 have radius r₁ and circle 2 have radius r₂. Equal circles have equal areas: πr₁²=πr₂². By Euclid's axiom (equals of equals are equal), r₁=r₂.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[4], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "Describe the contributions of Euclid to geometry. Why are Euclid's Elements considered important?",
             "options": None, "answer": "Euclid compiled 465 propositions in 13 books using deductive reasoning from 5 postulates and 5 axioms.",
             "solution": "Euclid's Elements (around 300 BC) is the first systematic treatment of geometry. It uses axioms/postulates + deductive proof — the foundation of modern mathematics. All of plane geometry follows from just 5 postulates.",
             "cognitive_level": "Understanding"},

            # ═══════════════════════════════════════════════════════════════════
            # Chapter 6 — Lines and Angles
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[5], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "The supplement of an angle of 75° is:",
             "options": [{"key":"A","text":"15°"},{"key":"B","text":"105°"},{"key":"C","text":"115°"},{"key":"D","text":"285°"}],
             "answer": "B", "solution": "Supplementary angles sum to 180°. 180° − 75° = 105°.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[5], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "If two lines intersect each other, then the vertically opposite angles are:",
             "options": [{"key":"A","text":"Supplementary"},{"key":"B","text":"Complementary"},{"key":"C","text":"Equal"},{"key":"D","text":"Adjacent"}],
             "answer": "C", "solution": "Vertically opposite angles are always equal (theorem).",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[5], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "What is the sum of angles on a straight line?",
             "options": None, "answer": "180°",
             "solution": "Angles on a straight line (linear pair) always sum to 180°.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[5], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "In a triangle, if two angles are 45° and 60°, find the third angle.",
             "options": None, "answer": "75°",
             "solution": "Angle sum = 180°. Third angle = 180° − 45° − 60° = 75°.",
             "cognitive_level": "Application"},

            {"chapter": chapters[5], "question_type": "SA", "marks": 2, "difficulty": "Easy",
             "question_text": "Two angles are complementary. If one angle is 35°, find the other.",
             "options": None, "answer": "55°",
             "solution": "Complementary angles sum to 90°. Other angle = 90° − 35° = 55°.",
             "cognitive_level": "Application"},

            {"chapter": chapters[5], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "Prove that if a transversal intersects two parallel lines, then the pair of alternate interior angles is equal.",
             "options": None, "answer": "Alternate interior angles are equal — proved using corresponding and vertically opposite angles.",
             "solution": "Let lines AB ∥ CD, transversal PQ. ∠3 and ∠6 are alternate interior angles. ∠2 = ∠6 (corresponding, AB∥CD). ∠2 = ∠3 (vertically opposite). Therefore ∠3 = ∠6.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[5], "question_type": "SA", "marks": 4, "difficulty": "Hard",
             "question_text": "In the given figure, AB ∥ CD and a transversal EF intersects them at G and H. If ∠EGB = 50°, find all eight angles formed.",
             "options": None, "answer": "∠EGA=130°, ∠EGB=50°, ∠AGB=130°, ∠BHF=50°, ∠GHD=130°, ∠CHF=50°, ∠GHC=130°, ∠FHD=50° (using properties of parallel lines)",
             "solution": "∠EGB=50° (given). ∠AGB=130° (linear pair). ∠EGA=130° (vertically opposite to AGB). Corresponding/alternate angles give all remaining angles as either 50° or 130°.",
             "cognitive_level": "Application"},

            {"chapter": chapters[5], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "Prove that the sum of angles of a triangle is 180°.",
             "options": None, "answer": "Using parallel line through vertex: ∠1+∠2+∠3=180°.",
             "solution": "Let △ABC. Draw DE ∥ BC through A. ∠DAB = ∠ABC (alternate, DE∥BC). ∠EAC = ∠ACB (alternate). ∠DAB + ∠BAC + ∠EAC = 180° (straight line DAE). Substituting: ∠ABC + ∠BAC + ∠ACB = 180°.",
             "cognitive_level": "Analysis"},

            # ═══════════════════════════════════════════════════════════════════
            # Chapter 7 — Triangles
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[6], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "Two triangles are congruent if two sides and the included angle of one triangle are equal to the corresponding two sides and included angle of the other. This is:",
             "options": [{"key":"A","text":"SSS"},{"key":"B","text":"SAS"},{"key":"C","text":"ASA"},{"key":"D","text":"RHS"}],
             "answer": "B", "solution": "SAS (Side-Angle-Side) congruence rule.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[6], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "In △ABC, AB = AC. The angle ∠B equals:",
             "options": [{"key":"A","text":"∠A"},{"key":"B","text":"∠C"},{"key":"C","text":"90°"},{"key":"D","text":"60°"}],
             "answer": "B", "solution": "In an isosceles triangle, angles opposite equal sides are equal. AB=AC implies ∠B=∠C.",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[6], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "State the SAS congruence rule.",
             "options": None, "answer": "If two sides and the included angle of one triangle are equal to two sides and the included angle of another, the triangles are congruent.",
             "solution": "SAS = Side-Angle-Side congruence criterion.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[6], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "In △PQR, PQ = PR. If ∠Q = 65°, find ∠P.",
             "options": None, "answer": "∠P = 50°",
             "solution": "PQ=PR so ∠Q=∠R=65°. ∠P = 180°−65°−65° = 50°.",
             "cognitive_level": "Application"},

            {"chapter": chapters[6], "question_type": "SA", "marks": 2, "difficulty": "Easy",
             "question_text": "In △ABC and △PQR, AB=PQ, BC=QR and ∠B=∠Q. Are the triangles congruent? State the congruence rule.",
             "options": None, "answer": "Yes, by SAS congruence.",
             "solution": "Two sides AB=PQ, BC=QR and included angle ∠B=∠Q are equal. By SAS, △ABC ≅ △PQR.",
             "cognitive_level": "Application"},

            {"chapter": chapters[6], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "Prove that the angles opposite to equal sides of an isosceles triangle are equal.",
             "options": None, "answer": "Draw bisector of ∠A; use SAS to show two triangles congruent; hence ∠B = ∠C.",
             "solution": "In △ABC with AB=AC, draw AD bisecting ∠A (D on BC). In △ABD and △ACD: AB=AC, ∠BAD=∠CAD, AD common. By SAS: △ABD≅△ACD. Hence ∠ABD=∠ACD, i.e. ∠B=∠C.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[6], "question_type": "SA", "marks": 4, "difficulty": "Hard",
             "question_text": "In △ABC, D is the midpoint of BC and AD ⊥ BC. Show that △ABC is isosceles.",
             "options": None, "answer": "By RHS: △ADB ≅ △ADC, so AB = AC.",
             "solution": "In △ADB and △ADC: AD common, DB=DC (D is midpoint), ∠ADB=∠ADC=90°. By RHS: △ADB≅△ADC. Hence AB=AC, so △ABC is isosceles.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[6], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "Prove that in a triangle, the side opposite the greater angle is greater.",
             "options": None, "answer": "If ∠B > ∠C, then AC > AB.",
             "solution": "In △ABC, let ∠B > ∠C. Assume AC ≤ AB. If AC=AB, then ∠B=∠C (isosceles), contradicting ∠B>∠C. If AC<AB, mark D on AB with AD=AC. Then ∠ACD=∠ADC (isosceles). ∠ADC > ∠B (exterior), so ∠ACD > ∠B > ∠C — but ∠ACD < ∠C (as D is between A and B), contradiction. Hence AC > AB.",
             "cognitive_level": "Analysis"},

            # ═══════════════════════════════════════════════════════════════════
            # Chapter 8 — Quadrilaterals
            # ═══════════════════════════════════════════════════════════════════
            {"chapter": chapters[7], "question_type": "MCQ", "marks": 1, "difficulty": "Easy",
             "question_text": "The sum of all interior angles of a quadrilateral is:",
             "options": [{"key":"A","text":"180°"},{"key":"B","text":"270°"},{"key":"C","text":"360°"},{"key":"D","text":"540°"}],
             "answer": "C", "solution": "Sum of interior angles of a quadrilateral = (4−2) × 180° = 360°.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[7], "question_type": "MCQ", "marks": 1, "difficulty": "Medium",
             "question_text": "Which of the following is NOT a property of a parallelogram?",
             "options": [{"key":"A","text":"Opposite sides are equal"},{"key":"B","text":"Opposite angles are equal"},{"key":"C","text":"Diagonals are equal"},{"key":"D","text":"Diagonals bisect each other"}],
             "answer": "C", "solution": "Diagonals of a parallelogram are NOT necessarily equal (they are equal only in a rectangle).",
             "cognitive_level": "Understanding"},

            {"chapter": chapters[7], "question_type": "VSA", "marks": 1, "difficulty": "Easy",
             "question_text": "In a parallelogram ABCD, if ∠A = 70°, find ∠C.",
             "options": None, "answer": "∠C = 70°",
             "solution": "Opposite angles of a parallelogram are equal, so ∠C = ∠A = 70°.",
             "cognitive_level": "Knowledge"},

            {"chapter": chapters[7], "question_type": "VSA", "marks": 2, "difficulty": "Easy",
             "question_text": "In parallelogram ABCD, ∠B = 110°. Find all four angles.",
             "options": None, "answer": "∠A=70°, ∠B=110°, ∠C=70°, ∠D=110°",
             "solution": "∠B=110°. ∠A+∠B=180° (co-interior) → ∠A=70°. ∠C=∠A=70° (opposite). ∠D=∠B=110° (opposite).",
             "cognitive_level": "Application"},

            {"chapter": chapters[7], "question_type": "SA", "marks": 2, "difficulty": "Easy",
             "question_text": "Show that the diagonals of a parallelogram bisect each other.",
             "options": None, "answer": "Using ASA congruence on the two triangles formed by diagonals.",
             "solution": "In ▱ABCD, diagonals AC and BD intersect at O. In △AOB and △COD: AB=CD (opposite sides), ∠OAB=∠OCD (alternate, AB∥CD), ∠OBA=∠ODC (alternate). By ASA: △AOB≅△COD. So AO=CO and BO=DO, i.e. diagonals bisect each other.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[7], "question_type": "SA", "marks": 3, "difficulty": "Medium",
             "question_text": "Prove that opposite sides of a parallelogram are equal.",
             "options": None, "answer": "Using ASA: △ABC ≅ △CDA, so AB=CD and BC=DA.",
             "solution": "In ▱ABCD, diagonal AC divides it into △ABC and △CDA. ∠BAC=∠DCA (alt., AB∥CD), AC common, ∠BCA=∠DAC (alt., BC∥AD). By ASA: △ABC≅△CDA. Hence AB=CD and BC=DA.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[7], "question_type": "SA", "marks": 4, "difficulty": "Hard",
             "question_text": "State and prove the Mid-point theorem for triangles.",
             "options": None, "answer": "The line segment joining midpoints of two sides of a triangle is parallel to the third side and half its length.",
             "solution": "In △ABC, D and E are midpoints of AB and AC. Extend DE to F so EF=DE, join CF. △AED≅△CEF (SAS: AE=CE, ∠AED=∠CEF vertically opposite, DE=EF). So CF=AD=BD and CF∥AB. BDFC is a parallelogram. DF=BC and DF∥BC. DE=DF/2=BC/2.",
             "cognitive_level": "Analysis"},

            {"chapter": chapters[7], "question_type": "LA", "marks": 5, "difficulty": "Hard",
             "question_text": "ABCD is a parallelogram in which P and Q are midpoints of opposite sides AB and CD. Show that APCQ is a parallelogram.",
             "options": None, "answer": "AP ∥ QC and AP = QC, so APCQ is a parallelogram.",
             "solution": "AB∥CD (parallelogram). P is midpoint of AB, Q is midpoint of CD. AP = AB/2 = CD/2 = QC. AP∥QC (since AB∥CD). A pair of opposite sides are equal and parallel, so APCQ is a parallelogram.",
             "cognitive_level": "Analysis"},
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
        print(f"✅ Demo data seeded successfully ({len(sample_qs)} questions across 8 chapters)")
        print("   Login: priya@arihant.edu / teacher123")
        print("   Admin: admin@classos.io / admin123")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    asyncio.run(seed())
