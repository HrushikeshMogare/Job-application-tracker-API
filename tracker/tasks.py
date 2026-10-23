import logging

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import Reminder

logger = logging.getLogger(__name__)


@shared_task
def send_due_reminders():
    """Email each due, incomplete reminder once. Runs on a schedule via Celery beat."""
    due = Reminder.objects.filter(
        due_at__lte=timezone.now(), is_completed=False, email_sent=False
    ).select_related("application__owner", "application__company")
    sent = 0
    for reminder in due:
        owner = reminder.application.owner
        if not owner.email:
            logger.warning("Reminder %s skipped: user has no email.", reminder.pk)
            continue
        send_mail(
            subject=f"Reminder: {reminder.get_reminder_type_display()} - {reminder.application.title}",
            message=(
                f"Your {reminder.get_reminder_type_display().lower()} reminder for "
                f"'{reminder.application.title}' at {reminder.application.company.name} is due."
            ),
            from_email=None,
            recipient_list=[owner.email],
        )
        reminder.email_sent = True
        reminder.save(update_fields=["email_sent"])
        sent += 1
    return sent
