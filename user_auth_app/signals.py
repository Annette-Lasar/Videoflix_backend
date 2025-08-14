
from django.conf import settings
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.db import transaction
from user_auth_app.tasks import (
    enqueue_activation_email,
    enqueue_password_reset_email,
    enqueue_plain_email,
)


User = get_user_model()

password_reset_requested = Signal()
password_reset_confirmed = Signal()



@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Signal-Receiver: feuert nach dem Anlegen eines Users."""
    if created and not instance.is_active:
        transaction.on_commit(lambda: enqueue_activation_email(instance.id))


@receiver(password_reset_requested)
def handle_password_reset_requested(sender, email, user, **kwargs):
    if user is not None:
        transaction.on_commit(lambda: enqueue_password_reset_email(user.id))
    else:
        subject = "Passwort zurücksetzen (Hinweis)"
        message = (
            "Hallo!\n\n"
            "Falls es zu dieser Adresse ein Konto gibt, erhältst du in Kürze eine E-Mail mit weiteren Schritten.\n"
            "Wenn du diese Nachricht unerwartet bekommst, kannst du sie ignorieren."
        )
        transaction.on_commit(lambda: enqueue_plain_email(email, subject, message))


@receiver(password_reset_confirmed)
def handle_password_reset_confirmed(sender, user, **kwargs):
    subject = "Password changed"
    message = (
        "Hello,\n\nYour password has been changed successfully.\n"
        "If you didn't perform this action, please contact support immediately."
    )
    transaction.on_commit(lambda: enqueue_plain_email(user.email, subject, message))
