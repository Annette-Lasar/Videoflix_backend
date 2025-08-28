import logging
import django_rq
from rq import Retry
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from utils.email_helpers import (
    send_activation_email,
    send_password_reset_email,
)

logger = logging.getLogger(__name__)


def send_activation_email_job(user_id: int) -> None:
    """
    RQ job: Send an activation email for the given user.
    Runs inside a worker process.
    """
    User = get_user_model()
    user = User.objects.get(pk=user_id)

    if not user.email:
        logger.warning(
            "Activation email skipped: user %s has no email", user_id)
        return

    send_activation_email(user)


def enqueue_activation_email(user_id: int) -> str:
    """
    Enqueue the activation email job into the default queue.
    Returns the job ID.
    """
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
    RQ job: Send a password reset email for the given user.
    Runs inside a worker process.
    """
    User = get_user_model()
    user = User.objects.get(pk=user_id)

    if not user.email:
        logger.warning("Password reset skipped: user %s has no email", user_id)
        return

    send_password_reset_email(user)


def send_plain_email_job(to_email: str, subject: str, message: str) -> None:
    """
    RQ job: Send a generic plain email (used when user may not exist).
    Runs inside a worker process.
    """
    if not to_email:
        logger.warning("Plain email skipped: empty recipient")
        return
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    send_mail(subject, message, from_email, [to_email], fail_silently=False)
    logger.info("Plain email sent to %s", to_email[:2] + "****")


def enqueue_password_reset_email(user_id: int) -> str:
    """
    Enqueue the password reset email job into the default queue.
    Returns the job ID.
    """
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
    """
    Enqueue a plain email job into the default queue.
    Returns the job ID.
    """
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
