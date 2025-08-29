import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from urllib.parse import urljoin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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
    subject = "Please activate Videoflix account!"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    to_email = user.email

    text_message = (
        f"Hi {user.username},\n\n"
        "Thanks for signing up with Videoflix!\n"
        "To activate your account, just click the link below:\n"
        f"{link}\n\n"
        "If you didn’t create this account, feel free to ignore this message.\n\n"
        "Warm regards,\nThe Videoflix Team"
    )

    html_message = render_to_string(
        "emails/confirm_email.html",
        {
            "user": user,
            "activation_url": link,
        }
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
    Includes both plain text (inline) and HTML (template) versions with the reset link.
    """
    reset_link = build_password_reset_link(user)
    subject = "Reset your Videoflix password"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    to_email = user.email

    text_message = (
        f"Hi {user.username},\n\n"
        "We received a request to reset your Videoflix password.\n"
        "To set a new password, just click the link below:\n"
        f"{reset_link}\n\n"
        "If you didn’t request this, please ignore this email.\n\n"
        "Best regards,\n"
        "The Videoflix Team"
    )

    html_message = render_to_string(
        "emails/password_reset.html",
        {
            "user": user,
            "reset_link": reset_link,
        }
    )

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to_email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=False)

    logger.info("Password reset email sent to %s", to_email[:2] + "****")


def send_password_changed_email(user):
    """
    Send confirmation email after password has been changed.
    """
    subject = "Password changed"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    to_email = user.email

    support_url = getattr(settings, "FRONTEND_ORIGIN", "#")

    context = {
        "user": user,
        "support_url": support_url,
    }

    text_message = (
        "Hello,\n\n"
        "Your password has been changed successfully.\n"
        f"If you didn't perform this action, please contact support: {support_url}\n\n"
        "Best regards,\n"
        "Your Videoflix Team."
    )

    html_message = render_to_string("emails/confirm_password_reset.html", context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to_email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=False)
