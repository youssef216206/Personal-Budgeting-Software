from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("transactions/add/", views.transaction_add, name="transaction_add"),
    path("budgets/", views.budget_list, name="budget_list"),
    path("budgets/add/", views.budget_create, name="budget_create"),
    path("budgets/<int:pk>/edit/", views.budget_edit, name="budget_edit"),
    path("goals/", views.goals_list, name="goals_list"),
    path("goals/add/", views.goal_create, name="goal_create"),
    path("goals/<int:pk>/contribute/", views.goal_contribute, name="goal_contribute"),
    path("reports/", views.reports, name="reports"),
    path("notifications/", views.notifications_view, name="notifications"),
]
