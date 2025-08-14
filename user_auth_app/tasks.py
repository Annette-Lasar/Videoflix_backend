import logging
import django_rq
from rq import Retry
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from utils.email_helpers import build_activation_link, build_password_reset_link

logger = logging.getLogger(__name__)


def send_activation_email_job(user_id: int) -> None:
    """RQ-Job: Aktivierungs-Mail verschicken (läuft im Worker)."""
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    if not user.email:
        logger.warning(
            "Activation email skipped: user %s has no email", user_id)
        return

    link = build_activation_link(user)
    subject = "Bitte Account aktivieren"
    message = (
        "Hallo!\n\n"
        "Bitte aktiviere deinen Account über folgenden Link:\n"
        f"{link}\n\n"
        "Vielen Dank!"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    send_mail(subject, message, from_email, [user.email], fail_silently=False)
    logger.info("Activation email queued->sent to %s", user.email[:2] + "****")


def enqueue_activation_email(user_id: int) -> str:
    """Wrapper: Job in die Queue legen (default-Queue beibehalten)."""
    q = django_rq.get_queue("default")
    job = q.enqueue(
        send_activation_email_job,
        user_id,
        job_timeout=15,
        retry=Retry(max=3, interval=[10, 60, 300]),
        result_ttl=3600,
        failure_ttl=7 * 24 * 3600,
        description=f"Activation email for user {user_id}",
    )
    return job.id


def send_password_reset_email_job(user_id: int) -> None:
    """
    Läuft im Worker: Passwort-Reset-Mail für EXISTIERENDEN User.
    Identischer Inhalt wie vorher (inkl. Link).
    """
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    if not user.email:
        logger.warning("Password reset skipped: user %s has no email", user_id)
        return

    link = build_password_reset_link(user)
    subject = "Passwort zurücksetzen"
    message = (
        "Hallo!\n\n"
        "Zum Zurücksetzen deines Passworts klicke auf den folgenden Link:\n"
        f"{link}\n\n"
        "Wenn du das nicht warst, ignoriere diese E-Mail."
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    send_mail(subject, message, from_email, [user.email], fail_silently=False)
    logger.info("Password reset email sent to %s", user.email[:2] + "****")


def send_plain_email_job(to_email: str, subject: str, message: str) -> None:
    """
    Läuft im Worker: Neutrale Mail (für 'User evtl. nicht vorhanden').
    """
    if not to_email:
        logger.warning("Plain email skipped: empty recipient")
        return
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    send_mail(subject, message, from_email, [to_email], fail_silently=False)
    logger.info("Plain email sent to %s", to_email[:2] + "****")


def enqueue_password_reset_email(user_id: int) -> str:
    q = django_rq.get_queue("default")
    job = q.enqueue(
        send_password_reset_email_job,
        user_id,
        job_timeout=15,
        retry=Retry(max=3, interval=[10, 60, 300]),
        failure_ttl=7 * 24 * 3600,
        description=f"Password reset email for user {user_id}",
    )
    return job.id


def enqueue_plain_email(to_email: str, subject: str, message: str) -> str:
    q = django_rq.get_queue("default")
    job = q.enqueue(
        send_plain_email_job,
        to_email, subject, message,
        job_timeout=15,
        retry=Retry(max=3, interval=[10, 60, 300]),
        failure_ttl=7 * 24 * 3600,
        description=f"Plain email to {to_email}",
    )
    return job.id
