from .serializers import RegistrationSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from rest_framework.response import Response
from rest_framework import status
from django.utils.encoding import force_str
from ..signals import password_reset_requested, password_reset_confirmed
from django.middleware.csrf import get_token

from django.contrib.auth import get_user_model


User = get_user_model()


class RegistrationView(APIView):
    """
    Handle user registration.

    Accepts user data, validates it with RegistrationSerializer, 
    saves the new account, and returns user info along with an activation token.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        saved_account = serializer.save()
        uidb64 = urlsafe_base64_encode(force_bytes(saved_account.pk))
        activation_token = default_token_generator.make_token(saved_account)

        data = {
            "user": {
                "id": saved_account.pk,
                "email": saved_account.email,
            },
            "token": activation_token,
        }

        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """
    Handle user login and JWT token generation.

    On successful authentication, sets access and refresh tokens 
    as HttpOnly cookies, issues a CSRF token, and returns basic user info.
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data["refresh"]
        access = serializer.validated_data["access"]
        user = serializer.user

        response = Response({"detail": "Login successful!"})

        response.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        response.data = {
            "detail": "Login successful!",
            "user": {
                "id": user.id,
                "username": user.username
            }
        }

        csrf_token = get_token(request)
        response.set_cookie(
            key="csrftoken",
            value=csrf_token,
            secure=True,
            samesite="Lax",
            path="/"
        )

        response.data = {
            "detail": "Login successful!",
            "user": {
                "id": user.id,
                "username": user.username
            }
        }

        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Handle JWT token refresh using the refresh token stored in cookies.

    Reads the refresh token from HttpOnly cookies, validates it,
    and issues a new access token which is also set as a cookie.
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {"detail": "Invalid refresh token!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get("access")

        response = Response({"detail": "Token refreshed!",
                             "access": access_token
                             })

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        return response


class ActivateAccountView(APIView):
    """
    Handle account activation via UID and token.

    Decodes the UID, verifies the token, and activates the user account
    if valid and not already active.
    """

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"message": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    Handle password reset requests.

    Accepts an email address, checks if a user exists for it,
    and sends the password_reset_requested signal.
    Always responds with a generic success message for security reasons.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()

        user = None
        if email:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                user = None

        password_reset_requested.send(
            sender=self.__class__,
            email=email,
            user=user,
        )

        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm and complete a password reset.

    Validates the UID and token, checks new passwords, enforces password validators,
    and updates the user's password if valid.
    """

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        pw1 = (request.data.get("new_password") or "").strip()
        pw2 = (request.data.get("confirm_password") or "").strip()
        if not pw1 or pw1 != pw2:
            return Response({"detail": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(pw1, user=user)
        except ValidationError as e:
            return Response({"detail": " ".join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(pw1)
        user.save(update_fields=["password"])

        password_reset_confirmed.send(sender=self.__class__, user=user)

        return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Handle user logout.

    Blacklists the refresh token if present and removes access/refresh cookies.
    Also issues a new CSRF token to the client.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is missing."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(
            {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK
        )

        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')

        csrf_token = get_token(request)
        response.set_cookie(
            key="csrftoken",
            value=csrf_token,
            secure=True,
            samesite="Lax",
            path="/"
        )

        return response
