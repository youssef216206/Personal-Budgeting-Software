"""URL routes for the budgeting app (included at site root)."""

from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/add/", views.transaction_add, name="transaction_add"),
    path("transactions/<int:pk>/edit/", views.transaction_edit, name="transaction_edit"),
    path("transactions/<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
    path("categories/", views.category_list, name="category_list"),
    path("subscriptions/", views.subscription_list, name="subscription_list"),
    path("subscriptions/add/", views.subscription_add, name="subscription_add"),
    path("subscriptions/<int:pk>/edit/", views.subscription_edit, name="subscription_edit"),
    path(
        "subscriptions/<int:pk>/delete/",
        views.subscription_delete,
        name="subscription_delete",
    ),
    path(
        "subscriptions/<int:pk>/toggle/",
        views.subscription_toggle,
        name="subscription_toggle",
    ),
    path("budgets/", views.budget_list, name="budget_list"),
    path("budgets/add/", views.budget_create, name="budget_create"),
    path("budgets/<int:pk>/edit/", views.budget_edit, name="budget_edit"),
    path("goals/", views.goals_list, name="goals_list"),
    path("goals/add/", views.goal_create, name="goal_create"),
    path("goals/<int:pk>/contribute/", views.goal_contribute, name="goal_contribute"),
    path("reports/", views.reports, name="reports"),
    path("notifications/", views.notifications_view, name="notifications"),
]
