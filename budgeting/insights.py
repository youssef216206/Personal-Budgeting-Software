"""Dashboard insight strings derived from budgets, transactions, and goals."""

from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone


def dashboard_insights(user, month_start, month_end, prev_month_start, prev_month_end):
    """Return up to three short dashboard tip strings.

    Args:
        user: Django user instance (the logged-in account).
        month_start: First day of the current reporting month.
        month_end: Last day of the current reporting month.
        prev_month_start: First day of the prior calendar month.
        prev_month_end: Last day of the prior calendar month.

    Returns:
        List of at most three human-readable insight strings.
    """
    from .models import Budget, SavingsGoal, Transaction

    tips = []

    expense_this = (
        Transaction.objects.filter(
            user=user,
            kind=Transaction.KIND_EXPENSE,
            occurred_at__date__gte=month_start,
            occurred_at__date__lte=month_end,
        ).aggregate(s=Sum("amount"))["s"]
        or 0
    )
    expense_prev = (
        Transaction.objects.filter(
            user=user,
            kind=Transaction.KIND_EXPENSE,
            occurred_at__date__gte=prev_month_start,
            occurred_at__date__lte=prev_month_end,
        ).aggregate(s=Sum("amount"))["s"]
        or 0
    )
    fi = float(expense_this)
    fp = float(expense_prev)
    if fp > 0:
        pct = (fi - fp) / fp * 100
        if pct > 5:
            tips.append(f"You spent {pct:.0f}% more this month than the previous calendar month.")
        elif pct < -5:
            tips.append(f"You spent {abs(pct):.0f}% less than the previous calendar month.")

    today = timezone.now().date()
    ending_soon = Budget.objects.filter(
        user=user,
        end_date__gte=today,
        end_date__lte=today + timedelta(days=7),
    ).count()
    if ending_soon:
        tips.append(f"{ending_soon} budget period(s) end in the next 7 days.")

    # Savings goal nearing completion
    for goal in SavingsGoal.objects.filter(user=user)[:15]:
        if goal.check_goal_completion():
            continue
        p = goal.get_progress_percentage()
        if p >= 80:
            tips.append(
                f"Goal '{goal.name}' is {p:.0f}% funded — a small bump could finish it soon."
            )
            break

    return tips[:3]
