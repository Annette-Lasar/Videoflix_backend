from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('token', response.data)

        user = User.objects.get(email="anna.bates@downton.com")
        self.assertTrue(user.check_password("securepassword123"))
        self.assertTrue(user.is_active)

    def test_registration_password_mismatch(self):
        data = {
            "email": "thomas.barrow@downton.com",
            "password": "secret123",
            "confirmed_password": "wrongconfirm"
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)


User = get_user_model()


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
