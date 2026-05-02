from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Spending/income category (global defaults or per-user custom)."""

    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories",
        help_text="Null = available to all users",
    )

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Notification(models.Model):
    """System alert persisted for a user (SDS US #5, #10)."""

    TYPE_WARNING = "warning"
    TYPE_ALERT = "alert"
    TYPE_INFO = "info"
    TYPE_SUCCESS = "success"
    TYPE_CHOICES = [
        (TYPE_WARNING, "Warning"),
        (TYPE_ALERT, "Alert"),
        (TYPE_INFO, "Info"),
        (TYPE_SUCCESS, "Success"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type}: {self.message[:60]}"

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=["is_read"])


class Budget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="budgets"
    )
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    alert_threshold_percent = models.PositiveSmallIntegerField(
        default=80, help_text="Notify when spent % reaches this value"
    )
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "category__name"]

    def __str__(self):
        return f"{self.user} · {self.category} ({self.start_date}–{self.end_date})"

    def spent_percentage(self):
        if not self.limit_amount or self.limit_amount == 0:
            return 0
        return float((self.spent_amount / self.limit_amount) * 100)

    def is_over_limit(self):
        return self.spent_amount > self.limit_amount

    def should_alert(self):
        pct = self.spent_percentage()
        return pct >= self.alert_threshold_percent or self.is_over_limit()

    def get_alert_message(self):
        if self.is_over_limit():
            return (
                f"Budget exceeded for {self.category.name}! "
                f"Spent {self.spent_amount} of {self.limit_amount}."
            )
        pct = self.spent_percentage()
        return (
            f"Budget warning for {self.category.name}: {pct:.0f}% used "
            f"({self.spent_amount} of {self.limit_amount})."
        )

    def trigger_alert(self):
        if self.should_alert():
            ntype = (
                Notification.TYPE_ALERT
                if self.is_over_limit()
                else Notification.TYPE_WARNING
            )
            Notification.objects.create(
                user_id=self.user_id,
                type=ntype,
                message=self.get_alert_message(),
            )


class Transaction(models.Model):
    KIND_INCOME = "income"
    KIND_EXPENSE = "expense"
    KIND_CHOICES = [(KIND_INCOME, "Income"), (KIND_EXPENSE, "Expense")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transactions",
    )
    description = models.CharField(max_length=255, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.kind} {self.amount} ({self.occurred_at.date()})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.kind == self.KIND_EXPENSE and self.category_id:
            on_date = self.occurred_at.date()
            matching = Budget.objects.filter(
                user=self.user,
                category=self.category,
                start_date__lte=on_date,
                end_date__gte=on_date,
            )
            for budget in matching:
                budget.spent_amount += self.amount
                budget.save(update_fields=["spent_amount"])
                budget.trigger_alert()


class SavingsGoal(models.Model):
    """User savings goal with progress tracking (SDS US #6)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="savings_goals",
    )
    name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_progress_percentage(self):
        if not self.target_amount or self.target_amount == 0:
            return 0
        pct = float((self.current_amount / self.target_amount) * 100)
        return min(pct, 100)

    def get_monthly_savings_needed(self):
        today = timezone.now().date()
        remaining = float(self.target_amount - self.current_amount)
        if remaining <= 0:
            return 0
        if self.deadline <= today:
            return remaining
        months = (
            (self.deadline.year - today.year) * 12
            + (self.deadline.month - today.month)
        )
        if months <= 0:
            return remaining
        return round(remaining / months, 2)

    def add_contribution(self, amount):
        self.current_amount += amount
        self.save(update_fields=["current_amount"])

    def check_goal_completion(self):
        return self.current_amount >= self.target_amount
