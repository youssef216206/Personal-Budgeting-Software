from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Budget, Category, SavingsGoal, Subscription, Transaction


class SignUpForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean(self):
        data = super().clean()
        p1 = data.get("password")
        p2 = data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("Please use a password with at least 8 characters.")
        return data


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["kind", "amount", "category", "description", "occurred_at"]
        widgets = {
            "occurred_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M:%S",
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs.setdefault("placeholder", "0.00")
        self.fields["amount"].widget.attrs.setdefault("step", "0.01")
        if user:
            self.fields["category"].queryset = Category.objects.filter(
                Q(user__isnull=True) | Q(user=user)
            ).order_by("name")
        f = self.fields["occurred_at"]
        f.widget.format = "%Y-%m-%dT%H:%M"
        f.input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]

    def clean(self):
        data = super().clean()
        kind = data.get("kind")
        amount = data.get("amount")

        if amount is not None and amount <= 0:
            self.add_error("amount", "Amount must be greater than zero.")

        if kind == Transaction.KIND_EXPENSE and not data.get("category"):
            self.add_error("category", "Expense transactions require a category.")

        return data


def transaction_form_voice_hidden(user):
    """Every field hidden — used to POST a browser-parsed voice phrase from the dashboard."""
    form = TransactionForm(user=user)
    for field in form.fields.values():
        field.widget = forms.HiddenInput()
    return form


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            "category",
            "limit_amount",
            "start_date",
            "end_date",
            "alert_threshold_percent",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, instance=None, **kwargs):
        self.user = user
        super().__init__(*args, instance=instance, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(
                Q(user__isnull=True) | Q(user=user)
            ).order_by("name")
        self.fields["limit_amount"].widget.attrs.setdefault("placeholder", "0.00")
        self.fields["limit_amount"].widget.attrs.setdefault("step", "0.01")

    def clean(self):
        data = super().clean()
        start = data.get("start_date")
        end = data.get("end_date")
        category = data.get("category")

        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after start date.")

        limit = data.get("limit_amount")
        if limit is not None and limit <= 0:
            self.add_error("limit_amount", "Budget limit must be greater than zero.")

        ath = data.get("alert_threshold_percent")
        if ath is not None and (ath < 1 or ath > 100):
            self.add_error(
                "alert_threshold_percent",
                "Alert threshold must be between 1 and 100.",
            )

        if self.user and category and start and end and not self.errors:
            qs = Budget.objects.filter(
                user=self.user,
                category=category,
                start_date__lte=end,
                end_date__gte=start,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A budget for this category already exists for this period "
                    "(overlapping dates)."
                )

        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user:
            obj.user = self.user
        if commit:
            obj.save()
        return obj


class SavingsGoalForm(forms.ModelForm):
    """Form for creating a savings goal (SDS US #6 GoalsUI.submitGoal)."""

    class Meta:
        model = SavingsGoal
        fields = ["name", "target_amount", "deadline"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_amount"].widget.attrs.setdefault("placeholder", "0.0")
        self.fields["target_amount"].widget.attrs.setdefault("step", "0.01")

    def clean_target_amount(self):
        amount = self.cleaned_data.get("target_amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Target amount must be greater than zero.")
        return amount

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        if deadline and deadline <= timezone.now().date():
            raise forms.ValidationError("Deadline must be a future date.")
        return deadline


class ContributionForm(forms.Form):
    """Form for adding a contribution to an existing goal (SDS US #6 GoalsUI.addContribution)."""

    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        label="Contribution amount",
        widget=forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01"}),
    )


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["name", "amount", "category", "cycle", "next_due", "is_active"]
        widgets = {
            "next_due": forms.DateInput(attrs={"type": "date"}),
            "name": forms.TextInput(attrs={"placeholder": "e.g. Netflix, Gym"}),
            "is_active": forms.CheckboxInput(
                attrs={"class": "sub-active-checkbox", "role": "switch"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs.setdefault("placeholder", "0.00")
        self.fields["amount"].widget.attrs.setdefault("step", "0.01")
        self.fields["is_active"].label = "Subscription active"
        self.fields[
            "is_active"
        ].help_text = "When paused, no automatic expense is posted until you resume."
        self.fields["next_due"].help_text = (
            "We add an expense when this date is today or earlier (runs right after you save)."
        )
        if user:
            self.fields["category"].queryset = Category.objects.filter(
                Q(user__isnull=True) | Q(user=user)
            ).order_by("name")

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user is not None:
            obj.user = self.user
        if commit:
            obj.save()
        return obj


class CategoryForm(forms.ModelForm):
    """Form for creating a personal category (defaults are read-only)."""

    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Coffee, Pets, Gym"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Category name is required.")
        if len(name) < 2:
            raise forms.ValidationError("Use at least 2 characters.")

        existing = Category.objects.filter(name__iexact=name)
        if self.user is not None:
            existing = existing.filter(Q(user__isnull=True) | Q(user=self.user))
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError(
                "That name is already taken (built-in or one of your categories)."
            )
        return name

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user is not None:
            obj.user = self.user
        if commit:
            obj.save()
        return obj
