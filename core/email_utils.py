from django.core.mail import send_mail
from django.conf import settings


def send_notification_email(subject, message, recipient_email):
    """
    Thin wrapper around Django's send_mail, so every notification
    call site doesn't repeat the same boilerplate. Fails silently
    if email sending breaks, so a notification failure never
    crashes the actual order/approval flow it's attached to.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=True,
        )
    except Exception:
        pass