from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from common.test_utils import create_owner, create_staff


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = create_owner()
        self.staff = create_staff()

    def test_login_returns_tokens(self):
        response = self.client.post('/api/auth/login/', {
            'email': self.owner.email,
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'owner')

    def test_protected_endpoint_requires_auth(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_access_me(self):
        login = self.client.post('/api/auth/login/', {
            'email': self.staff.email,
            'password': 'testpass123',
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.staff.email)

    def test_change_password(self):
        login = self.client.post('/api/auth/login/', {
            'email': self.owner.email,
            'password': 'testpass123',
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = self.client.post('/api/auth/change-password/', {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
