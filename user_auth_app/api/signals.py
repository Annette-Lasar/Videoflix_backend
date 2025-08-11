
from django.conf import settings
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import get_user_model

User = get_user_model()

password_reset_requested = Signal()


def build_activation_link(user):
    """Erzeugt den Link, den deine activate.html versteht."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    path = f"/pages/auth/activate.html?uid={uidb64}&token={token}"
        
    return f"/pages/auth/activate.html?uid={uidb64}&token={token}"


def send_activation_email(user):
    """Verschickt die Aktivierungs-E-Mail an den User."""
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
    

def build_password_reset_link(user):
    pass


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Signal-Receiver: feuert nach dem Anlegen eines Users."""
    if created and not instance.is_active:
        send_activation_email(instance)


@receiver(password_reset_requested)
def handle_password_reset_requested(sender, email, user, **kwargs):
    pass