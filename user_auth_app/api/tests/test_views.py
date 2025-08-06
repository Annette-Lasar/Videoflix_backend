from rest_framework.test import APITestCase
from rest_framework import status
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
