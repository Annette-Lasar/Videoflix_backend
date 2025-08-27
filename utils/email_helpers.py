import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from urllib.parse import urljoin
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def build_activation_link(user) -> str:
    """Erzeugt einen (möglichst) absoluten Link für die Aktivierung."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    base = getattr(settings, "FRONTEND_ORIGIN", "http://127.0.0.1:5500")
    path = f"/pages/auth/activate.html?uid={uidb64}&token={token}"

    return urljoin(base, path)


def send_activation_email(user):
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
    Relativer Link (Option A), host-unabhängig und Bootcamp-sicher.
    Die Frontend-Seite liest uid/token aus der URL und ruft /api/password_confirm/<uid>/<token>/ auf.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"/pages/auth/password_confirm.html?uid={uidb64}&token={token}"


def send_password_reset_email(user):
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
