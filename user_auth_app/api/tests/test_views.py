from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('register')

    def test_registration_success(self):
        data = {
            "email": "anna.bates@downton.com",
            "password": "securepassword123",
            "confirmed_password": "securepassword123"
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('user', response.data)
        self.assertIn('token', response.data)
        self.assertIsInstance(response.data['token'], str)
        self.assertTrue(len(response.data['token']) > 0)

        user = User.objects.get(email="anna.bates@downton.com")
        self.assertTrue(user.check_password("securepassword123"))
        self.assertFalse(user.is_active)

        self.assertEqual(response.data['user']['id'], user.pk)
        self.assertEqual(response.data['user']['email'], user.email)

    def test_registration_password_mismatch(self):
        data = {
            "email": "thomas.barrow@downton.com",
            "password": "secret123",
            "confirmed_password": "wrongconfirm"
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)


class LoginViewTest(APITestCase):
    def setUp(self):
        self.login_url = reverse('login')
        self.email = "testuser@example.com"
        self.password = "securepassword"

        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password
        )

    def test_login_success(self):
        data = {"email": self.email, "password": self.password}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], self.email)

    def test_login_with_wrong_password(self):
        data = {"email": self.email, "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

    def test_login_with_missing_fields(self):
        data = {"email": self.email}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, 400)


class CookieTokenRefreshViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('token_refresh')  # Name in urls.py prüfen
        self.user = User.objects.create_user(
            username="refreshuser@example.com",
            email="refreshuser@example.com",
            password="supersecure"
        )

        refresh = RefreshToken.for_user(self.user)
        self.valid_refresh_token = str(refresh)
        self.invalid_refresh_token = "invalid.token.string"

    def test_missing_refresh_token_cookie(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Refresh token not found!")

    def test_invalid_refresh_token_cookie(self):
        self.client.cookies["refresh_token"] = self.invalid_refresh_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Invalid refresh token!")

    def test_valid_refresh_token_cookie(self):
        self.client.cookies["refresh_token"] = self.valid_refresh_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["detail"], "Token refreshed!")
        self.assertIn("access_token", response.cookies)


class ActivateAccountViewTests(APITestCase):
    def setUp(self):
        self.password = "S3cureP@ss!"
        self.user = User.objects.create_user(
            username="anna",
            email="anna@example.com",
            password=self.password,
            is_active=False,
        )

        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def test_activation_success(self):
        url = reverse("activate", kwargs={
                      "uidb64": self.uidb64, "token": self.token})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get("message"),
                         "Account successfully activated.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_activation_invalid_token(self):
        url = reverse("activate", kwargs={
                      "uidb64": self.uidb64, "token": "not-a-real-token"})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("message"), "Invalid or expired token.")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_activation_invalid_uid(self):
        bad_uid = "bogus"
        url = reverse("activate", kwargs={
                      "uidb64": bad_uid, "token": self.token})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("message"), "Invalid activation link.")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class PasswordResetRequestViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("password_reset")
        self.user_email = "anna@example.com"
        self.password = "TestPass123"
        self.user = User.objects.create_user(
            username="anna",
            email=self.user_email,
            password=self.password,
            is_active=True
        )

    def test_password_reset_existing_user(self):
        """Is supposed to return 200 and to send email if user exists."""
        response = self.client.post(
            self.url, {"email": self.user_email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("detail"),
                         "An email has been sent to reset your password.")

        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user_email, mail.outbox[0].to)

    def test_password_reset_nonexistent_user(self):
        """Is supposed to return 200 anyway and send a neutral email if user doesn't exist."""
        non_existing_email = "doesnotexist@example.com"
        response = self.client.post(
            self.url, {"email": non_existing_email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("detail"),
                         "An email has been sent to reset your password.")

        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(non_existing_email, mail.outbox[0].to)


class PasswordResetConfirmViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="oldpassword123",
            is_active=True,
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.url = reverse(
            "password_confirm",
            kwargs={"uidb64": self.uidb64, "token": self.token},
        )

    def test_reset_password_success(self):
        data = {
            "new_password": "newsecurepassword123",
            "confirm_password": "newsecurepassword123"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "Your Password has been successfully reset."
        )

        # Prüfen, ob das neue Passwort wirklich gesetzt wurde
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepassword123"))

    def test_passwords_do_not_match(self):
        data = {
            "new_password": "pw1",
            "confirm_password": "pw2"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        

class LogoutViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('logout')
        self.user = User.objects.create_user(
            username="logoutuser@example.com",
            email="logoutuser@example.com",
            password="securelogout"
        )
        refresh = RefreshToken.for_user(self.user)
        self.valid_refresh_token = str(refresh)
        self.invalid_refresh_token = "fake.token.value"

    def test_missing_refresh_token_cookie(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Missing refresh token!")

    def test_invalid_refresh_token_cookie(self):
        self.client.cookies["refresh_token"] = self.invalid_refresh_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Invalid token.")

    def test_valid_refresh_token_cookie(self):
        self.client.cookies["refresh_token"] = self.valid_refresh_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["detail"],
            "Logout successful! All tokens will be deleted. Refresh token is now invalid."
        )

        self.assertEqual(response.cookies["access_token"]["max-age"], 0)
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)
