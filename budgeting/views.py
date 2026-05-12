"""HTTP views: authentication, dashboard, CRUD flows, and reports."""

import calendar
import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    BudgetForm,
    CategoryForm,
    ContributionForm,
    SavingsGoalForm,
    SignUpForm,
    SubscriptionForm,
    TransactionForm,
    transaction_form_voice_hidden,
)
from .models import (
    Budget,
    Category,
    Notification,
    SavingsGoal,
    Subscription,
    Transaction,
)


def signup(request):
    """Show signup form; on POST create user, log in, redirect to dashboard."""
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
    """Login page using ``budgeting/login.html``."""

    template_name = "budgeting/login.html"
    redirect_authenticated_user = True


@login_required
def dashboard(request):
    """Main dashboard: KPIs, charts, budgets, voice quick-add."""
    user = request.user
    month_start = date.today().replace(day=1)
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

    category_breakdown = list(
        Transaction.objects.filter(
            user=user,
            kind=Transaction.KIND_EXPENSE,
            occurred_at__date__gte=month_start,
            occurred_at__date__lte=month_end,
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    # Donut: at most 11 slices; merge 11th-ranked and below into one "Other categories" slice
    _chart_cat_max_slices = 11
    if len(category_breakdown) > _chart_cat_max_slices:
        _top_rows = category_breakdown[: _chart_cat_max_slices - 1]
        _tail_total = sum(
            float(r["total"] or 0)
            for r in category_breakdown[_chart_cat_max_slices - 1 :]
        )
        chart_category_rows = list(_top_rows)
        if _tail_total > 0:
            chart_category_rows.append(
                {"category__name": "Other categories", "total": _tail_total}
            )
    else:
        chart_category_rows = category_breakdown
    chart_cat_labels = [
        (row["category__name"] or "Uncategorized") for row in chart_category_rows
    ]
    chart_cat_data = [float(row["total"]) for row in chart_category_rows]

    daily_rows = (
        Transaction.objects.filter(
            user=user,
            kind=Transaction.KIND_EXPENSE,
            occurred_at__date__gte=month_start,
            occurred_at__date__lte=month_end,
        )
        .annotate(day=TruncDate("occurred_at"))
        .values("day")
        .annotate(total=Sum("amount"))
    )
    by_day = {r["day"]: float(r["total"]) for r in daily_rows}
    days_in_month = (month_end - month_start).days + 1
    daily_series = []
    for i in range(days_in_month):
        d = month_start + timedelta(days=i)
        daily_series.append({"day": d, "total": by_day.get(d, 0.0)})
    chart_day_labels = [d["day"].strftime("%b %d") for d in daily_series]
    chart_day_data = [d["total"] for d in daily_series]

    has_chart_data = any(v > 0 for v in chart_cat_data) or any(
        v > 0 for v in chart_day_data
    )

    voice_categories_json = json.dumps(
        list(
            Category.objects.filter(Q(user__isnull=True) | Q(user=user))
            .order_by("name")
            .values("id", "name")
        )
    )

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
            "has_chart_data": has_chart_data,
            "chart_cat_labels": json.dumps(chart_cat_labels),
            "chart_cat_data": json.dumps(chart_cat_data),
            "chart_day_labels": json.dumps(chart_day_labels),
            "chart_day_data": json.dumps(chart_day_data),
            "voice_categories_json": voice_categories_json,
            "voice_quick_form": transaction_form_voice_hidden(user),
        },
    )


@login_required
def transaction_add(request):
    """GET: empty form. POST: save income/expense and surface budget alerts."""
    voice_categories_json = json.dumps(
        list(
            Category.objects.filter(Q(user__isnull=True) | Q(user=request.user))
            .order_by("name")
            .values("id", "name")
        )
    )
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
            if request.POST.get("next") == "dashboard":
                return redirect("dashboard")
            return redirect("transaction_list")
        if request.POST.get("next") == "dashboard":
            for field, errs in form.errors.items():
                for msg in errs:
                    name = "Transaction" if field == "__all__" else field.replace("_", " ").title()
                    messages.error(request, f"{name}: {msg}")
            return redirect("dashboard")
    else:
        form = TransactionForm(user=request.user)
    return render(
        request,
        "budgeting/transaction_form.html",
        {
            "form": form,
            "heading": "Add transaction",
            "submit_label": "Save transaction",
            "back_url_name": "dashboard",
            "voice_categories_json": voice_categories_json,
        },
    )


@login_required
def transaction_list(request):
    """Filterable, paginated list with per-filter income/expense totals."""
    user = request.user
    qs = Transaction.objects.filter(user=user).select_related("category")

    kind = request.GET.get("kind", "").strip()
    category_id = request.GET.get("category", "").strip()
    from_date_str = request.GET.get("from_date", "").strip()
    to_date_str = request.GET.get("to_date", "").strip()
    q = request.GET.get("q", "").strip()

    if kind in (Transaction.KIND_INCOME, Transaction.KIND_EXPENSE):
        qs = qs.filter(kind=kind)
    if category_id.isdigit():
        qs = qs.filter(category_id=int(category_id))
    from_date = None
    to_date = None
    if from_date_str:
        try:
            from_date = date.fromisoformat(from_date_str)
            qs = qs.filter(occurred_at__date__gte=from_date)
        except ValueError:
            from_date = None
    if to_date_str:
        try:
            to_date = date.fromisoformat(to_date_str)
            qs = qs.filter(occurred_at__date__lte=to_date)
        except ValueError:
            to_date = None
    if q:
        qs = qs.filter(description__icontains=q)

    totals = qs.aggregate(
        income=Sum("amount", filter=Q(kind=Transaction.KIND_INCOME)),
        expense=Sum("amount", filter=Q(kind=Transaction.KIND_EXPENSE)),
    )

    available_categories = Category.objects.filter(
        Q(user__isnull=True) | Q(user=user)
    ).order_by("name")

    has_filters = any([kind, category_id, from_date_str, to_date_str, q])

    return render(
        request,
        "budgeting/transaction_list.html",
        {
            "transactions": qs,
            "available_categories": available_categories,
            "filter_kind": kind,
            "filter_category": category_id,
            "filter_from_date": from_date_str,
            "filter_to_date": to_date_str,
            "filter_q": q,
            "filter_count": qs.count(),
            "filter_income": totals["income"] or 0,
            "filter_expense": totals["expense"] or 0,
            "has_filters": has_filters,
        },
    )


@login_required
def transaction_edit(request, pk):
    """Edit an existing transaction owned by the current user."""
    t = get_object_or_404(Transaction, pk=pk, user=request.user)

    voice_categories_json = json.dumps(
        list(
            Category.objects.filter(Q(user__isnull=True) | Q(user=request.user))
            .order_by("name")
            .values("id", "name")
        )
    )
    if request.method == "POST":
        form = TransactionForm(request.POST, instance=t, user=request.user)
        if form.is_valid():
            before_save = timezone.now()
            form.save()
            new_alerts = Notification.objects.filter(
                user=request.user, created_at__gte=before_save
            )
            for alert in new_alerts:
                messages.warning(request, alert.message)
            messages.success(request, "Transaction updated.")
            return redirect("transaction_list")
    else:
        form = TransactionForm(instance=t, user=request.user)
    return render(
        request,
        "budgeting/transaction_form.html",
        {
            "form": form,
            "heading": "Edit transaction",
            "submit_label": "Save changes",
            "back_url_name": "transaction_list",
            "transaction": t,
            "voice_categories_json": voice_categories_json,
        },
    )


@login_required
def transaction_delete(request, pk):
    """Confirm on GET; POST deletes the transaction."""
    t = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == "POST":
        t.delete()
        messages.success(request, "Transaction deleted.")
        return redirect("transaction_list")
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])
    return render(
        request,
        "budgeting/transaction_confirm_delete.html",
        {"transaction": t},
    )


@login_required
def category_list(request):
    """List global default categories and the user's custom ones; POST adds custom."""
    user = request.user
    if request.method == "POST":
        form = CategoryForm(request.POST, user=user)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' added.")
            return redirect("category_list")
    else:
        form = CategoryForm(user=user)

    defaults = Category.objects.filter(user__isnull=True).order_by("name")
    mine = Category.objects.filter(user=user).order_by("name")

    return render(
        request,
        "budgeting/category_list.html",
        {
            "form": form,
            "defaults": defaults,
            "mine": mine,
        },
    )


@login_required
def subscription_list(request):
    """All subscriptions for the logged-in user."""
    items = Subscription.objects.filter(user=request.user).select_related("category")
    return render(request, "budgeting/subscription_list.html", {"subscriptions": items})


def _subscription_save_message(request, saved_verb: str):
    """After save, post any due subscription expenses and surface one clear toast."""
    posted = Subscription.objects.process_due_for(request.user)
    if posted:
        names = ", ".join(posted[:6])
        more = "…" if len(posted) > 6 else ""
        messages.success(
            request,
            f"{saved_verb}. Posted expense(s): {names}{more}.",
        )
    else:
        messages.success(request, saved_verb + ".")


@login_required
def subscription_add(request):
    """Create subscription; may immediately post due charges."""
    if request.method == "POST":
        form = SubscriptionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            _subscription_save_message(request, "Subscription saved")
            return redirect("subscription_list")
    else:
        form = SubscriptionForm(
            user=request.user,
            initial={"next_due": timezone.now().date()},
        )
    return render(
        request,
        "budgeting/subscription_form.html",
        {"form": form, "heading": "Add subscription"},
    )


@login_required
def subscription_edit(request, pk):
    """Update subscription; may post catch-up charges after save."""
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=sub, user=request.user)
        if form.is_valid():
            form.save()
            _subscription_save_message(request, "Subscription updated")
            return redirect("subscription_list")
    else:
        form = SubscriptionForm(instance=sub, user=request.user)
    return render(
        request,
        "budgeting/subscription_form.html",
        {"form": form, "heading": "Edit subscription", "subscription": sub},
    )


@login_required
def subscription_delete(request, pk):
    """Confirm on GET; POST removes the subscription row only (not past transactions)."""
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == "POST":
        sub.delete()
        messages.success(request, "Subscription deleted.")
        return redirect("subscription_list")
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])
    return render(
        request,
        "budgeting/subscription_confirm_delete.html",
        {"subscription": sub},
    )


@login_required
def subscription_toggle(request, pk):
    """Pause or resume automatic posting (POST only)."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    sub.is_active = not sub.is_active
    sub.save(update_fields=["is_active"])
    messages.info(
        request,
        "Subscription resumed." if sub.is_active else "Subscription paused.",
    )
    return redirect("subscription_list")


@login_required
def budget_list(request):
    """Budget cards for the user."""
    items = Budget.objects.filter(user=request.user).select_related("category")
    return render(request, "budgeting/budget_list.html", {"budgets": items})


@login_required
def budget_create(request):
    """Show budget form; POST validates and saves."""
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
    """Edit budget limits and dates for one row."""
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
    """Savings goals overview."""
    goals = SavingsGoal.objects.filter(user=request.user)
    return render(request, "budgeting/goals_list.html", {"goals": goals})


@login_required
def goal_create(request):
    """Create a new :class:`~budgeting.models.SavingsGoal`."""
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
    """Add money toward a goal; may emit a completion notification."""
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
    """Date-range report with category breakdown and simple narrative insights."""
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
    """List all notifications and mark unread ones as read."""
    all_notifs = Notification.objects.filter(user=request.user)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "budgeting/notifications.html", {"notifications": all_notifs})
