from celery import shared_task

from .emails import ActivationReminderEmail
from .models import User


@shared_task
def send_activation_reminders():
    """Daily reminder for users who registered but haven't activated their account."""
    inactive_users = User.objects.filter(is_active=False).exclude(email="")

    sent = 0
    for user in inactive_users:
        ActivationReminderEmail(context={"user": user}).send([user.email])
        sent += 1

    return sent
