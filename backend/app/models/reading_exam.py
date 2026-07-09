"""Schemas for the Reading module, modelled on the real Trinity ISE II
Reading & Writing paper: Task 1 (Long Reading), Task 2 (Multi-text Reading)
and Task 3 (Reading into Writing).

Every exercise type has a *Public* variant (sent to the frontend, no
answers) and an *Internal* variant (kept server-side, carries the answer
key). This mirrors how the real exam works: the candidate never sees the
mark scheme.
"""

import datetime as dt
from typing import Literal

from pydantic import BaseModel

from app.models.schemas import ErrorItem


class Labelled(BaseModel):
    id: str
    text: str


# ---------------------------------------------------------------- Matching

class MatchingExercisePublic(BaseModel):
    kind: Literal["matching"] = "matching"
    instructions: str
    items: list[Labelled]
    options: list[Labelled]
    allow_repeat_options: bool = False


class MatchingExerciseInternal(MatchingExercisePublic):
    correct: dict[str, str]  # item_id -> option_id


# -------------------------------------------------------------- True/False

class TrueFalseExercisePublic(BaseModel):
    kind: Literal["true_false"] = "true_false"
    instructions: str
    statements: list[Labelled]


class TrueFalseExerciseInternal(TrueFalseExercisePublic):
    correct: dict[str, bool]  # statement_id -> True/False


# ------------------------------------------------------- Multi-select (N of M)

class MultiSelectExercisePublic(BaseModel):
    kind: Literal["multi_select"] = "multi_select"
    instructions: str
    options: list[Labelled]
    select_count: int


class MultiSelectExerciseInternal(MultiSelectExercisePublic):
    correct: list[str]  # option ids that are true


# ------------------------------------------------ Gap fill (free text, AI-graded)

class GapFillExercisePublic(BaseModel):
    kind: Literal["gap_fill"] = "gap_fill"
    instructions: str
    items: list[Labelled]


class GapFillExerciseInternal(GapFillExercisePublic):
    accepted_answers: dict[str, list[str]]  # item_id -> acceptable phrasings


# -------------------------------------------------------------------- Task 1

class ReadingTask1Public(BaseModel):
    title: str
    paragraphs: list[Labelled]
    exercise_a: MatchingExercisePublic
    exercise_b: GapFillExercisePublic
    exercise_c: TrueFalseExercisePublic
    exercise_d: GapFillExercisePublic


class ReadingTask1Internal(BaseModel):
    title: str
    paragraphs: list[Labelled]
    exercise_a: MatchingExerciseInternal
    exercise_b: GapFillExerciseInternal
    exercise_c: TrueFalseExerciseInternal
    exercise_d: GapFillExerciseInternal

    def to_public(self) -> ReadingTask1Public:
        return ReadingTask1Public(
            title=self.title,
            paragraphs=self.paragraphs,
            exercise_a=MatchingExercisePublic(**self.exercise_a.model_dump(exclude={"correct"})),
            exercise_b=GapFillExercisePublic(**self.exercise_b.model_dump(exclude={"accepted_answers"})),
            exercise_c=TrueFalseExercisePublic(**self.exercise_c.model_dump(exclude={"correct"})),
            exercise_d=GapFillExercisePublic(**self.exercise_d.model_dump(exclude={"accepted_answers"})),
        )


class Task1Submission(BaseModel):
    exercise_a: dict[str, str]
    exercise_b: dict[str, str]
    exercise_c: dict[str, bool]
    exercise_d: dict[str, str]


# -------------------------------------------------------------------- Task 2

class ReadingTask2Public(BaseModel):
    title: str
    texts: list[Labelled]
    exercise_a: MatchingExercisePublic
    exercise_b: MultiSelectExercisePublic
    exercise_c: GapFillExercisePublic


class ReadingTask2Internal(BaseModel):
    title: str
    texts: list[Labelled]
    exercise_a: MatchingExerciseInternal
    exercise_b: MultiSelectExerciseInternal
    exercise_c: GapFillExerciseInternal

    def to_public(self) -> ReadingTask2Public:
        return ReadingTask2Public(
            title=self.title,
            texts=self.texts,
            exercise_a=MatchingExercisePublic(**self.exercise_a.model_dump(exclude={"correct"})),
            exercise_b=MultiSelectExercisePublic(**self.exercise_b.model_dump(exclude={"correct"})),
            exercise_c=GapFillExercisePublic(**self.exercise_c.model_dump(exclude={"accepted_answers"})),
        )


class Task2Submission(BaseModel):
    exercise_a: dict[str, str]
    exercise_b: list[str]
    exercise_c: dict[str, str]


# -------------------------------------------------------------------- Task 3

class ReadingTask3Public(BaseModel):
    title: str
    texts: list[Labelled]
    exercise_1_5: MatchingExercisePublic
    exercise_6_10: MultiSelectExercisePublic


class ReadingTask3Internal(BaseModel):
    title: str
    texts: list[Labelled]
    exercise_1_5: MatchingExerciseInternal
    exercise_6_10: MultiSelectExerciseInternal

    def to_public(self) -> ReadingTask3Public:
        return ReadingTask3Public(
            title=self.title,
            texts=self.texts,
            exercise_1_5=MatchingExercisePublic(**self.exercise_1_5.model_dump(exclude={"correct"})),
            exercise_6_10=MultiSelectExercisePublic(**self.exercise_6_10.model_dump(exclude={"correct"})),
        )


class Task3Submission(BaseModel):
    exercise_1_5: dict[str, str]
    exercise_6_10: list[str]


# --------------------------------------------------------------- Whole exam

class ReadingExamPublic(BaseModel):
    id: str
    source: Literal["fixed", "generated"]
    task1: ReadingTask1Public
    task2: ReadingTask2Public
    task3: ReadingTask3Public


class ReadingExamInternal(BaseModel):
    id: str
    source: Literal["fixed", "generated"]
    task1: ReadingTask1Internal
    task2: ReadingTask2Internal
    task3: ReadingTask3Internal

    def to_public(self) -> ReadingExamPublic:
        return ReadingExamPublic(
            id=self.id,
            source=self.source,
            task1=self.task1.to_public(),
            task2=self.task2.to_public(),
            task3=self.task3.to_public(),
        )


class ReadingExamSubmission(BaseModel):
    exam_id: str
    task1: Task1Submission
    task2: Task2Submission
    task3: Task3Submission
    duration_seconds: int


# ------------------------------------------------------------------ Results

class ItemFeedback(BaseModel):
    id: str
    correct: bool
    expected: str | None = None
    comment: str | None = None


class ExerciseResult(BaseModel):
    label: str
    correct_count: int
    total_count: int
    items: list[ItemFeedback]


class TaskResult(BaseModel):
    task_number: int
    title: str
    exercises: list[ExerciseResult]
    correct_count: int
    total_count: int


class ReadingExamResult(BaseModel):
    session_id: int
    overall_score: float
    band: str
    summary: str
    tasks: list[TaskResult]
    errors: list[ErrorItem]
    created_at: dt.datetime
