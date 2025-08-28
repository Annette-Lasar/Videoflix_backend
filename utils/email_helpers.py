import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from urllib.parse import urljoin
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def build_activation_link(user) -> str:
    """
    Build an absolute activation link for a given user.

    The link includes the uid and token as query parameters
    and points to the frontend activation page.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    base = getattr(settings, "FRONTEND_ORIGIN", "http://127.0.0.1:5500")
    path = f"/pages/auth/activate.html?uid={uidb64}&token={token}"

    return urljoin(base, path)


def send_activation_email(user):
    """
    Send an activation email to the given user.

    Includes both plain text and HTML versions with the activation link.
    """
    link = build_activation_link(user)
    subject = "Bitte den Videoflix-Account aktivieren!"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    to_email = user.email

    text_message = (
        "Hallo!\n\n"
        "Bitte aktiviere deinen Account über folgenden Link:\n"
        f"{link}\n\n"
        "Vielen Dank!"
    )

    html_message = (
        f"<p>Hallo!</p>"
        f"<p>Bitte aktiviere deinen Account über folgenden Link:<br>"
        f'<a href="{link}">{link}</a></p>'
        f"<p>Vielen Dank!</p>"
    )

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to_email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=False)

    logger.info("Activation email sent to %s", to_email[:2] + "****")


def build_password_reset_link(user):
    """
    Build an absolute password reset link for a given user.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base = getattr(settings, "FRONTEND_ORIGIN", "http://127.0.0.1:5500")
    path = f"/pages/auth/confirm_password.html?uid={uidb64}&token={token}"
    return urljoin(base, path)


def send_password_reset_email(user):
    """
    Send a password reset email to the given user.

    Includes both plain text and HTML versions with the reset link.
    """
    link = build_password_reset_link(user)
    subject = "Passwort zurücksetzen"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    to_email = user.email

    text_message = (
        "Hallo!\n\n"
        "Zum Zurücksetzen deines Passworts klicke auf den folgenden Link:\n"
        f"{link}\n\n"
        "Wenn du das nicht warst, ignoriere diese E-Mail."
    )

    html_message = (
        f"<p>Hallo!</p>"
        f"<p>Zum Zurücksetzen deines Passworts klicke auf folgenden Link:<br>"
        f'<a href="{link}">{link}</a></p>'
        f"<p>Wenn du das nicht warst, ignoriere diese E-Mail.</p>"
    )

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to_email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=False)

    logger.info("Password reset email sent to %s", to_email[:2] + "****")
