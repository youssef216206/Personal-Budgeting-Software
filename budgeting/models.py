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
    spent_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
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

    @classmethod
    def apply_expense_to_matching(cls, user, category, amount, on_date):
        qs = cls.objects.filter(
            user=user,
            category=category,
            start_date__lte=on_date,
            end_date__gte=on_date,
        )
        for budget in qs:
            budget.spent_amount += amount
            budget.save(update_fields=["spent_amount"])


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
            Budget.apply_expense_to_matching(
                self.user, self.category, self.amount, self.occurred_at.date()
            )
