"""Aggregate financial-health score with a simple weighted breakdown."""

import math
from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone


def compute_health(user):
    """Compute a simple 0–100 financial health score and UI hints.

    Weights savings rate, staying within active budgets, savings-goal progress,
    and how consistently the user logs transactions (last 30 days).

    Args:
        user: Django user instance.

    Returns:
        dict: Keys ``score``, ``breakdown``, ``tips``, ``savings_note``,
        and SVG ring helpers ``ring_r``, ``ring_circ``, ``ring_offset``.
    """
    from .models import Budget, SavingsGoal, Transaction

    today = timezone.now().date()
    start30 = today - timedelta(days=30)

    qs = Transaction.objects.filter(user=user, occurred_at__date__gte=start30)
    income = (
        qs.filter(kind=Transaction.KIND_INCOME).aggregate(s=Sum("amount"))["s"] or 0
    )
    expense = (
        qs.filter(kind=Transaction.KIND_EXPENSE).aggregate(s=Sum("amount"))["s"] or 0
    )

    savings_pts = 0.0
    fi = float(income)
    fe = float(expense)
    if fi <= 0 and fe <= 0:
        savings_note = "Log income and expenses to score your savings rate."
    elif fi <= 0:
        savings_note = "Add income in the last 30 days so we can measure savings rate."
    else:
        rate = (fi - fe) / fi
        savings_pts = max(0, min(40, rate * 40))
        savings_note = f"Savings trend (last 30d): income {fi:.2f}, expenses {fe:.2f}."

    # Budget adherence among active budgets
    active = Budget.objects.filter(
        user=user, start_date__lte=today, end_date__gte=today
    )
    adherence_pts = 0.0
    if active.exists():
        ok = sum(1 for b in active if not b.is_over_limit())
        adherence_pts = (ok / active.count()) * 30

    goals = SavingsGoal.objects.filter(user=user)
    goal_pts = 0.0
    if goals.exists():
        total_prog = sum(g.get_progress_percentage() for g in goals)
        avg = total_prog / goals.count()
        goal_pts = min(20, avg * 0.2)

    n_days = (
        Transaction.objects.filter(user=user, occurred_at__date__gte=start30)
        .annotate(day=TruncDate("occurred_at"))
        .values("day")
        .distinct()
        .count()
    )
    activity_pts = min(10, n_days * (10 / 12))

    breakdown = [
        {"label": "Savings posture (vs income)", "points": round(savings_pts, 1)},
        {"label": "Budget adherence", "points": round(adherence_pts, 1)},
        {"label": "Goal momentum", "points": round(goal_pts, 1)},
        {"label": "Logging consistency", "points": round(activity_pts, 1)},
    ]
    raw = savings_pts + adherence_pts + goal_pts + activity_pts
    score = int(round(min(100, raw)))

    tips = []
    if savings_pts < 15 and fi > fe:
        tips.append("Increasing income categories or trimming top expenses lifts your score fastest.")
    active_budgets = Budget.objects.filter(
        user=user, start_date__lte=today, end_date__gte=today
    )
    overs = sum(1 for b in active_budgets if b.is_over_limit())
    if overs:
        tips.append(f"{overs} budget(s) are currently over limit — adjust spending or limits.")
    elif adherence_pts < 15 and active.exists():
        tips.append("Stay inside each budget through the period to raise your adherence score.")

    if activity_pts < 5:
        tips.append("Log expenses on more days — consistency earns easy points.")

    R = 52
    circumference = round(2 * math.pi * R, 3)
    ring_dash_offset = round(circumference * (1 - score / 100.0), 3)

    return {
        "score": score,
        "breakdown": breakdown,
        "tips": tips[:2],
        "savings_note": savings_note,
        "ring_r": R,
        "ring_circ": circumference,
        "ring_offset": ring_dash_offset,
    }
