from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from urllib.parse import urljoin
from django.core.mail import send_mail


def build_activation_link(user) -> str:
    """Erzeugt einen (möglichst) absoluten Link für die Aktivierung."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    base = getattr(settings, "FRONTEND_ORIGIN", "http://localhost:8001")
    path = f"/pages/auth/activate.html?uid={uidb64}&token={token}"

    return urljoin(base, path)


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
    """
    Relativer Link (Option A), host-unabhängig und Bootcamp-sicher.
    Die Frontend-Seite liest uid/token aus der URL und ruft /api/password_confirm/<uid>/<token>/ auf.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"/pages/auth/password_confirm.html?uid={uidb64}&token={token}"
