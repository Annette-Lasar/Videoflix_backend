from django.test import TestCase
from user_auth_app.api.serializers import RegistrationSerializer, LoginSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationSerializerTest(TestCase):
    def test_valid_serializer_creates_user(self):
        data = {
            "email": "anna@domain.com",
            "password": "supersecurepassword",
            "confirmed_password": "supersecurepassword"
        }

        serializer = RegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()
        self.assertEqual(user.email, data["email"])
        self.assertTrue(user.check_password(data["password"]))
        self.assertFalse(user.is_active)

    def test_serializer_rejects_mismatched_passwords(self):
        data = {
            "email": "anna@domain.com",
            "password": "pass1",
            "confirmed_password": "pass2"
        }

        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_serializer_rejects_example_domain(self):
        data = {
            "email": "user@example.com",
            "password": "pass123",
            "confirmed_password": "pass123"
        }

        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_serializer_rejects_duplicate_email(self):
        User.objects.create_user(
            email="duplicate@domain.com",
            username="duplicate@domain.com",
            password="testpass"
        )

        data = {
            "email": "duplicate@domain.com",
            "password": "pass123",
            "confirmed_password": "pass123"
        }

        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)



class LoginSerializerTest(TestCase):
    def setUp(self):
        self.email = "serializer@example.com"
        self.password = "verysecure123"
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password
        )

    def test_login_valid_credentials(self):
        data = {"email": self.email, "password": self.password}
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn("access", serializer.validated_data)
        self.assertIn("refresh", serializer.validated_data)
        self.assertEqual(serializer.user, self.user)

    def test_login_invalid_email(self):
        data = {"email": "wrong@example.com", "password": self.password}
        serializer = LoginSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Invalid email or password.", str(context.exception))

    def test_login_wrong_password(self):
        data = {"email": self.email, "password": "wrongpassword"}
        serializer = LoginSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Invalid email or password.", str(context.exception))