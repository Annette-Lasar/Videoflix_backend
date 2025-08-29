
from django.conf import settings
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.db import transaction
from user_auth_app.tasks import (
    enqueue_activation_email,
    enqueue_password_reset_email,
    enqueue_plain_email,
    enqueue_password_changed_email
)

from utils.email_helpers import send_password_changed_email


User = get_user_model()

password_reset_requested = Signal()
password_reset_confirmed = Signal()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Signal receiver: when a new (inactive) user is created, enqueue an activation email after the transaction commits."""
    if created and not instance.is_active:
        transaction.on_commit(lambda: enqueue_activation_email(instance.id))


@receiver(password_reset_requested)
def handle_password_reset_requested(sender, email, user, **kwargs):
    """Handle a password-reset request: enqueue a reset email if the user exists; otherwise send a neutral notice to the provided address."""
    if user is not None:
        transaction.on_commit(lambda: enqueue_password_reset_email(user.id))
    else:
        subject = "Password reset (notice)"
        message = (
            "Hello,\n\n"
            "If an account exists for this email address, you will receive an email with further instructions shortly.\n"
            "If you did not request this, you can safely ignore this message."
        )
        transaction.on_commit(
            lambda: enqueue_plain_email(email, subject, message))


# @receiver(password_reset_confirmed)
# def handle_password_reset_confirmed(sender, user, **kwargs):
#     """After a successful password reset/confirmation, notify the user with a plain confirmation email."""
#     subject = "Password changed"
#     message = (
#         "Hello,\n\nYour password has been changed successfully.\n"
#         "If you didn't perform this action, please contact support immediately."
#     )
#     transaction.on_commit(lambda: enqueue_plain_email(
#         user.email, subject, message))


@receiver(password_reset_confirmed)
def handle_password_reset_confirmed(sender, user, **kwargs):
    """After a successful password reset/confirmation, notify the user with a confirmation email."""
    transaction.on_commit(lambda: enqueue_password_changed_email(user.id))

