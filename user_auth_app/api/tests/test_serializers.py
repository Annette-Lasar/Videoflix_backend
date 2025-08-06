from django.test import TestCase
from user_auth_app.api.serializers import RegistrationSerializer
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
        self.assertTrue(user.is_active)

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
