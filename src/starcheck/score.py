"""Weighted scoring: 28 checks -> one number and a letter grade."""

from __future__ import annotations

from dataclasses import dataclass, field

from starcheck.checks import DIMENSIONS, FACTOR

GRADES = [
    (95, "A+"),
    (88, "A"),
    (78, "B+"),
    (70, "B"),
    (55, "C"),
    (35, "D"),
    (0, "E"),
]


@dataclass
class Result:
    score: int
    grade: str
    earned: float
    total: int
    by_dim: dict = field(default_factory=dict)
    checks: list = field(default_factory=list)
    skipped: int = 0

    @property
    def failed(self) -> list:
        order = {"fail": 0, "warn": 1, "pass": 2, "skip": 3}
        todo = [c for c in self.checks if c.status in ("fail", "warn")]
        return sorted(todo, key=lambda c: (-c.weight, order[c.status]))

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "grade": self.grade,
            "earned": round(self.earned, 2),
            "total_weight": self.total,
            "skipped": self.skipped,
            "dimensions": self.by_dim,
            "checks": [c.as_dict() for c in self.checks],
        }


def grade_for(score: int) -> str:
    for floor, label in GRADES:
        if score >= floor:
            return label
    return "E"


def score(checks: list) -> Result:
    earned = 0.0
    total = 0
    by_dim = {}
    skipped = 0

    for c in checks:
        dim = by_dim.setdefault(c.dimension, {"label": DIMENSIONS[c.dimension][0], "earned": 0.0, "total": 0})
        if c.status == "skip":
            skipped += 1
            continue
        factor = FACTOR.get(c.status, 0.0)
        earned += c.weight * factor
        total += c.weight
        dim["earned"] += c.weight * factor
        dim["total"] += c.weight

    value = round(100 * earned / total) if total else 0
    for dim in by_dim.values():
        dim["score"] = round(100 * dim["earned"] / dim["total"]) if dim["total"] else None
        dim["earned"] = round(dim["earned"], 2)

    return Result(
        score=value,
        grade=grade_for(value),
        earned=earned,
        total=total,
        by_dim=by_dim,
        checks=checks,
        skipped=skipped,
    )
