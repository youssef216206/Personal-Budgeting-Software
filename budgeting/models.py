import calendar
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.db import models, transaction
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
        constraints = [
            models.UniqueConstraint(
                fields=["name", "user"],
                name="uniq_category_name_per_user",
            ),
        ]

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

    @staticmethod
    def _matching_budgets(user, category_id, on_date):
        if not category_id or on_date is None:
            return Budget.objects.none()
        return Budget.objects.filter(
            user=user,
            category_id=category_id,
            start_date__lte=on_date,
            end_date__gte=on_date,
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_snapshot = None
        if not is_new:
            try:
                prev = Transaction.objects.select_for_update().get(pk=self.pk)
                old_snapshot = {
                    "kind": prev.kind,
                    "amount": prev.amount,
                    "category_id": prev.category_id,
                    "on_date": prev.occurred_at.date() if prev.occurred_at else None,
                    "user_id": prev.user_id,
                }
            except Transaction.DoesNotExist:
                old_snapshot = None

        super().save(*args, **kwargs)

        if old_snapshot and old_snapshot["kind"] == self.KIND_EXPENSE:
            for b in self._matching_budgets(
                self.user_id, old_snapshot["category_id"], old_snapshot["on_date"]
            ):
                b.spent_amount = max(0, b.spent_amount - old_snapshot["amount"])
                b.save(update_fields=["spent_amount"])

        if self.kind == self.KIND_EXPENSE and self.category_id:
            on_date = self.occurred_at.date() if self.occurred_at else None
            triggered = []
            for budget in self._matching_budgets(self.user_id, self.category_id, on_date):
                budget.spent_amount += self.amount
                budget.save(update_fields=["spent_amount"])
                triggered.append(budget)
            for budget in triggered:
                budget.trigger_alert()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        if self.kind == self.KIND_EXPENSE and self.category_id and self.occurred_at:
            on_date = self.occurred_at.date()
            for b in self._matching_budgets(self.user_id, self.category_id, on_date):
                b.spent_amount = max(0, b.spent_amount - self.amount)
                b.save(update_fields=["spent_amount"])
        return super().delete(*args, **kwargs)


class SubscriptionManager(models.Manager):
    def process_due_for(self, user, max_iter_per_subscription=72):
        today = timezone.now().date()
        posted = []
        with transaction.atomic():
            qs = (
                self.filter(user=user, is_active=True, next_due__lte=today)
                .select_related("category")
                .select_for_update()
            )
            for sub in qs:
                n_left = max_iter_per_subscription
                next_due = sub.next_due
                while sub.is_active and next_due <= today and n_left > 0:
                    occurred = timezone.make_aware(datetime.combine(next_due, time(12, 0)))
                    Transaction.objects.create(
                        user_id=sub.user_id,
                        kind=Transaction.KIND_EXPENSE,
                        amount=sub.amount,
                        category_id=sub.category_id,
                        description=f"Subscription · {sub.name}",
                        occurred_at=occurred,
                    )
                    posted.append(sub.name)
                    next_due = Subscription.advance_date(next_due, sub.cycle)
                    n_left -= 1
                self.filter(pk=sub.pk).update(next_due=next_due)
        return posted


class Subscription(models.Model):
    """Recurring subscription or bill charge (processed on dashboard load)."""

    CYCLE_WEEKLY = "weekly"
    CYCLE_MONTHLY = "monthly"
    CYCLE_YEARLY = "yearly"
    CYCLE_CHOICES = [
        (CYCLE_WEEKLY, "Weekly"),
        (CYCLE_MONTHLY, "Monthly"),
        (CYCLE_YEARLY, "Yearly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    cycle = models.CharField(max_length=10, choices=CYCLE_CHOICES, default=CYCLE_MONTHLY)
    next_due = models.DateField(help_text="Next charge date; advances after posting")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["next_due", "name"]

    def __str__(self):
        return f"{self.name} ({self.cycle})"

    @classmethod
    def advance_date(cls, from_date, cycle: str):
        d = from_date if isinstance(from_date, date) else datetime.combine(from_date, time.min).date()
        if cycle == cls.CYCLE_WEEKLY:
            return d + timedelta(weeks=1)
        if cycle == cls.CYCLE_MONTHLY:
            y, m, day = d.year, d.month, d.day
            if m == 12:
                y, m = y + 1, 1
            else:
                m += 1
            last = calendar.monthrange(y, m)[1]
            return date(y, m, min(day, last))
        if cycle == cls.CYCLE_YEARLY:
            try:
                return d.replace(year=d.year + 1)
            except ValueError:
                return date(d.year + 1, 2, 28)
        return d

    objects = SubscriptionManager()


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
