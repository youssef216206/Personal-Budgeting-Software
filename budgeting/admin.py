from django.contrib import admin

from .models import Budget, Category, Notification, SavingsGoal, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user")


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "limit_amount", "spent_amount", "start_date", "end_date")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "amount", "category", "occurred_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "message", "is_read", "created_at")
    list_filter = ("type", "is_read")


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "target_amount", "current_amount", "deadline")
