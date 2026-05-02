import calendar
import json
from datetime import date

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BudgetForm, ContributionForm, SavingsGoalForm, SignUpForm, TransactionForm
from .models import Budget, Notification, SavingsGoal, Transaction


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["full_name"][:150],
            )
            user = User.objects.get(username__iexact=email)
            login(request, user)
            messages.success(request, "Welcome! Your account was created.")
            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "budgeting/signup.html", {"form": form})


class UserLoginView(LoginView):
    template_name = "budgeting/login.html"
    redirect_authenticated_user = True


@login_required
def dashboard(request):
    user = request.user
    today = date.today()
    month_start = today.replace(day=1)
    month_end = month_start.replace(
        day=calendar.monthrange(month_start.year, month_start.month)[1]
    )

    recent_transactions = Transaction.objects.filter(user=user).select_related("category")[:8]
    budgets = list(Budget.objects.filter(user=user).select_related("category"))

    # Full calendar month (not "through today") so future-dated rows in this month still count.
    income_total = (
        Transaction.objects.filter(
            user=user,
            kind=Transaction.KIND_INCOME,
            occurred_at__date__gte=month_start,
            occurred_at__date__lte=month_end,
        ).aggregate(s=Sum("amount"))["s"]
        or 0
    )
    expense_total = (
        Transaction.objects.filter(
            user=user,
            kind=Transaction.KIND_EXPENSE,
            occurred_at__date__gte=month_start,
            occurred_at__date__lte=month_end,
        ).aggregate(s=Sum("amount"))["s"]
        or 0
    )

    income_all = (
        Transaction.objects.filter(user=user, kind=Transaction.KIND_INCOME).aggregate(
            s=Sum("amount")
        )["s"]
        or 0
    )
    expense_all = (
        Transaction.objects.filter(user=user, kind=Transaction.KIND_EXPENSE).aggregate(
            s=Sum("amount")
        )["s"]
        or 0
    )
    total_balance = float(income_all) - float(expense_all)

    budget_warnings = [b for b in budgets if b.should_alert()]
    unread_notifications = Notification.objects.filter(user=user, is_read=False)
    has_data = Transaction.objects.filter(user=user).exists()
    savings_goals = SavingsGoal.objects.filter(user=user)[:5]

    return render(
        request,
        "budgeting/dashboard.html",
        {
            "recent_transactions": recent_transactions,
            "budgets": budgets,
            "income_total": income_total,
            "expense_total": expense_total,
            "total_balance": total_balance,
            "budget_warnings": budget_warnings,
            "unread_notifications": unread_notifications,
            "has_data": has_data,
            "savings_goals": savings_goals,
            "month": month_start.strftime("%B %Y"),
        },
    )


@login_required
def transaction_add(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            t = form.save(commit=False)
            t.user = request.user
            before_save = timezone.now()
            t.save()
            new_alerts = Notification.objects.filter(
                user=request.user, created_at__gte=before_save
            )
            for alert in new_alerts:
                messages.warning(request, alert.message)
            messages.success(request, "Transaction saved successfully.")
            return redirect("dashboard")
    else:
        form = TransactionForm(user=request.user)
    return render(request, "budgeting/transaction_form.html", {"form": form})


@login_required
def budget_list(request):
    items = Budget.objects.filter(user=request.user).select_related("category")
    return render(request, "budgeting/budget_list.html", {"budgets": items})


@login_required
def budget_create(request):
    if request.method == "POST":
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget saved.")
            return redirect("budget_list")
    else:
        form = BudgetForm(user=request.user)
    return render(
        request,
        "budgeting/budget_form.html",
        {"form": form, "heading": "Create budget"},
    )


@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == "POST":
        form = BudgetForm(request.POST, user=request.user, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget updated.")
            return redirect("budget_list")
    else:
        form = BudgetForm(user=request.user, instance=budget)
    return render(
        request,
        "budgeting/budget_form.html",
        {"form": form, "heading": "Edit budget"},
    )


@login_required
def goals_list(request):
    goals = SavingsGoal.objects.filter(user=request.user)
    return render(request, "budgeting/goals_list.html", {"goals": goals})


@login_required
def goal_create(request):
    if request.method == "POST":
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            goal = SavingsGoal.objects.create(
                user=request.user,
                name=form.cleaned_data["name"],
                target_amount=form.cleaned_data["target_amount"],
                deadline=form.cleaned_data["deadline"],
            )
            messages.success(request, f"Goal '{goal.name}' created.")
            return redirect("goals_list")
    else:
        form = SavingsGoalForm()
    return render(request, "budgeting/goal_form.html", {"form": form, "heading": "Create goal"})


@login_required
def goal_contribute(request, pk):
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    if request.method == "POST":
        form = ContributionForm(request.POST)
        if form.is_valid():
            was_complete = goal.check_goal_completion()
            goal.add_contribution(form.cleaned_data["amount"])
            if goal.check_goal_completion() and not was_complete:
                Notification.objects.create(
                    user=request.user,
                    type=Notification.TYPE_SUCCESS,
                    message=(
                        f'Congratulations on achieving your goal "{goal.name}"! '
                        "Great work staying on track."
                    ),
                )
                messages.success(
                    request,
                    f"Congratulations! You have reached your goal '{goal.name}'!",
                )
            else:
                messages.success(
                    request,
                    f"Contribution added. Progress: {goal.get_progress_percentage():.0f}%",
                )
            return redirect("goals_list")
    else:
        form = ContributionForm()
    return render(request, "budgeting/goal_contribute.html", {"form": form, "goal": goal})


@login_required
def reports(request):
    today = date.today()
    default_from = today.replace(day=1).isoformat()
    default_to = today.isoformat()

    from_date_str = request.GET.get("from_date", default_from)
    to_date_str = request.GET.get("to_date", default_to)

    try:
        from_date = date.fromisoformat(from_date_str)
        to_date = date.fromisoformat(to_date_str)
        if to_date < from_date:
            raise ValueError("to_date before from_date")
    except (ValueError, AttributeError):
        from_date = today.replace(day=1)
        to_date = today

    user = request.user
    transactions = Transaction.objects.filter(
        user=user,
        occurred_at__date__gte=from_date,
        occurred_at__date__lte=to_date,
    )

    breakdown = list(
        transactions.filter(kind=Transaction.KIND_EXPENSE)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    total_income = (
        transactions.filter(kind=Transaction.KIND_INCOME).aggregate(s=Sum("amount"))["s"]
        or 0
    )
    total_expenses = (
        transactions.filter(kind=Transaction.KIND_EXPENSE).aggregate(s=Sum("amount"))["s"]
        or 0
    )

    insights = []
    if not transactions.exists():
        insights.append("No transaction data available for this period.")
    else:
        balance = float(total_income) - float(total_expenses)
        if balance > 0:
            insights.append(f"You saved {balance:.2f} this period. Great job!")
        elif balance < 0:
            insights.append(f"You overspent by {abs(balance):.2f} this period.")
        else:
            insights.append("Income and expenses balanced out this period.")
        if breakdown:
            top = breakdown[0]
            cat_name = top["category__name"] or "Uncategorized"
            insights.append(
                f"Highest spending category: {cat_name} ({float(top['total']):.2f})."
            )

    chart_labels = json.dumps([b["category__name"] or "Uncategorized" for b in breakdown])
    chart_data = json.dumps([float(b["total"]) for b in breakdown])

    return render(
        request,
        "budgeting/reports.html",
        {
            "from_date": from_date,
            "to_date": to_date,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": float(total_income) - float(total_expenses),
            "breakdown": breakdown,
            "insights": insights,
            "has_data": transactions.exists(),
            "chart_labels": chart_labels,
            "chart_data": chart_data,
        },
    )


@login_required
def notifications_view(request):
    all_notifs = Notification.objects.filter(user=request.user)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "budgeting/notifications.html", {"notifications": all_notifs})
