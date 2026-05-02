from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BudgetForm, SignUpForm, TransactionForm
from .models import Budget, Transaction


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
    recent = Transaction.objects.filter(user=request.user)[:8]
    budgets = Budget.objects.filter(user=request.user)[:12]
    income_total = (
        Transaction.objects.filter(user=request.user, kind=Transaction.KIND_INCOME).aggregate(
            s=Sum("amount")
        )["s"]
        or 0
    )
    expense_total = (
        Transaction.objects.filter(user=request.user, kind=Transaction.KIND_EXPENSE).aggregate(
            s=Sum("amount")
        )["s"]
        or 0
    )
    return render(
        request,
        "budgeting/dashboard.html",
        {
            "recent_transactions": recent,
            "budgets": budgets,
            "income_total": income_total,
            "expense_total": expense_total,
        },
    )


@login_required
def transaction_add(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            t = form.save(commit=False)
            t.user = request.user
            t.save()
            messages.success(request, "Transaction saved successfully.")
            return redirect("dashboard")
    else:
        form = TransactionForm(user=request.user)
    return render(request, "budgeting/transaction_form.html", {"form": form})


@login_required
def budget_list(request):
    items = Budget.objects.filter(user=request.user)
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
