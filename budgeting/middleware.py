"""Request-scoped side effects for logged-in users."""

from django.contrib import messages

from .models import Subscription


class ProcessDueSubscriptionsMiddleware:
    """
    Post due subscription charges as expense transactions (same as dashboard did).
    Runs on any authenticated page so balance and reports stay correct without
    visiting the dashboard first.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            posted = Subscription.objects.process_due_for(request.user)
            if posted:
                names = ", ".join(posted[:6])
                more = "…" if len(posted) > 6 else ""
                messages.success(
                    request,
                    f"Posted {len(posted)} subscription charge(s): {names}{more}",
                )
        return self.get_response(request)
