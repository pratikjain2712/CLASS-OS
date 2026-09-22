"""
Abstraction layer for loading questions from JSON or database.
Controlled by USE_JSON_DATA environment variable.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.questions import Question, QuestionUsage


@dataclass
class QuestionData:
    """In-memory representation of a question for JSON mode."""
    id: uuid.UUID
    chapter_number: int
    chapter_name: str
    question_type: str
    marks: int
    difficulty: str
    question_text: str
    answer: str
    usage_count: int = 0
    is_approved: bool = True

    def to_dict(self):
        return {
            "id": self.id,
            "chapter_number": self.chapter_number,
            "chapter_name": self.chapter_name,
            "question_type": self.question_type,
            "marks": self.marks,
            "difficulty": self.difficulty,
            "question_text": self.question_text,
            "answer": self.answer,
            "usage_count": self.usage_count,
            "is_approved": self.is_approved,
        }


class JSONDataLoader:
    """Load questions from JSON file."""

    _instance = None
    _data: list[QuestionData] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self) -> list[QuestionData]:
        """Load questions from JSON file (cached in memory)."""
        if self._loaded and self._data:
            return self._data

        json_path = Path(__file__).parent.parent.parent / "data" / "cbse_class9_math_clean.json"

        if not json_path.exists():
            raise FileNotFoundError(f"Question data file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self._data = []
        for item in raw_data:
            q = QuestionData(
                id=uuid.uuid4(),  # Generate unique ID for in-memory use
                chapter_number=item.get("chapter_number", 0),
                chapter_name=item.get("chapter_name", ""),
                question_type=item.get("q_type", ""),
                marks=item.get("marks", 0),
                difficulty=item.get("difficulty", ""),
                question_text=item.get("question_text", ""),
                answer=item.get("answer", ""),
                usage_count=0,
                is_approved=True,
            )
            self._data.append(q)

        self._loaded = True
        return self._data

    def filter(
        self,
        chapter_numbers: Optional[list[int]] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        marks: Optional[int] = None,
        limit: int = 50,
    ) -> list[QuestionData]:
        """Filter questions by criteria."""
        data = self.load()

        results = data

        if chapter_numbers:
            results = [q for q in results if q.chapter_number in chapter_numbers]

        if difficulty:
            results = [q for q in results if q.difficulty.lower() == difficulty.lower()]

        if question_type:
            results = [q for q in results if q.question_type.upper() == question_type.upper()]

        if marks:
            results = [q for q in results if q.marks == marks]

        # Sort by usage_count, then random for consistency
        results = sorted(results, key=lambda x: x.usage_count)

        return results[:limit]

    def get_by_chapter_type_marks(
        self,
        chapter_numbers: list[int],
        question_type: str,
        marks: int,
        difficulty: Optional[str] = None,
        exclude_ids: Optional[set[uuid.UUID]] = None,
    ) -> list[QuestionData]:
        """Get questions matching specific criteria (for paper generation)."""
        data = self.load()
        exclude_ids = exclude_ids or set()

        results = [
            q for q in data
            if q.chapter_number in chapter_numbers
            and q.question_type.upper() == question_type.upper()
            and q.marks == marks
            and q.id not in exclude_ids
            and q.is_approved
        ]

        if difficulty and difficulty != "Mixed":
            results = [q for q in results if q.difficulty.lower() == difficulty.lower()]

        # Sort by usage_count (prefer less used questions)
        results = sorted(results, key=lambda x: x.usage_count)
        return results

    def count_by_criteria(
        self,
        chapter_numbers: list[int],
        question_type: str,
        marks: int,
        difficulty: Optional[str] = None,
        exclude_ids: Optional[set[uuid.UUID]] = None,
    ) -> int:
        """Count questions matching criteria."""
        return len(
            self.get_by_chapter_type_marks(
                chapter_numbers, question_type, marks, difficulty, exclude_ids
            )
        )


class DataLoaderFactory:
    """Factory to get the appropriate data loader based on environment."""

    _use_json = os.getenv("USE_JSON_DATA", "false").lower() == "true"
    _json_loader = JSONDataLoader() if _use_json else None

    @classmethod
    def use_json(cls) -> bool:
        """Check if JSON mode is enabled."""
        return cls._use_json

    @classmethod
    def get_json_loader(cls) -> JSONDataLoader:
        """Get JSON data loader (for JSON mode)."""
        if not cls._use_json:
            raise RuntimeError("JSON data loader not enabled. Set USE_JSON_DATA=true")
        return cls._json_loader

    @classmethod
    def initialize(cls):
        """Initialize the data loader based on environment."""
        if cls._use_json:
            try:
                cls._json_loader.load()
                print("✓ JSON data loader initialized with questions from JSON file")
            except Exception as e:
                print(f"✗ Failed to load JSON data: {e}")
                raise
