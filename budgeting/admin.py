"""Django admin registrations for budgeting models."""

from django.contrib import admin

from .models import Budget, Category, Notification, SavingsGoal, Subscription, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """List and search helpers for :class:`~budgeting.models.Category`."""



@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Admin columns for budget periods and spend."""



@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Subscription billing schedule overview."""



@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Transaction ledger columns."""



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """In-app notifications with type and read filters."""

    list_filter = ("type", "is_read")


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    """Savings targets and progress."""

