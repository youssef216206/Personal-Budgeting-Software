from .models import Notification


def unread_notifications(request):
    """Unread count plus ``nav_url_name`` for highlighting the current nav link."""
    nav = ""
    rm = getattr(request, "resolver_match", None)
    if rm is not None and rm.url_name:
        nav = rm.url_name

    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            "unread_notification_count": count,
            "nav_url_name": nav,
        }
    return {"unread_notification_count": 0, "nav_url_name": nav}
