import tempfile
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings

from users.forms import ProfileForm
from users.models import User

TEST_MEDIA_ROOT = tempfile.mkdtemp()


def variant_templates(variant: str):
    base = Path(settings.BASE_DIR)
    return [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [base / f'templates_var{variant}'],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }
    ]


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, TASK_VERSION='1', TEMPLATES=variant_templates('1'))
class AuthFlowTests(TestCase):
    def test_register_login_and_logout(self):
        response = self.client.post(
            '/users/register/',
            {
                'name': 'Иван',
                'surname': 'Иванов',
                'email': 'ivan@example.com',
                'password': 'secret12345',
            },
        )
        self.assertRedirects(response, '/users/login/')
        self.assertTrue(User.objects.filter(email='ivan@example.com').exists())

        response = self.client.post('/users/login/', {'email': 'ivan@example.com', 'password': 'secret12345'})
        self.assertRedirects(response, '/projects/list')

        response = self.client.get('/users/logout/')
        self.assertRedirects(response, '/projects/list')

    def test_profile_form_normalizes_phone_and_validates_github(self):
        user = User.objects.create_user(
            email='user@example.com', password='password', name='User', surname='One'
        )
        form = ProfileForm(
            data={
                'name': 'User',
                'surname': 'One',
                'about': 'Hello',
                'phone': '89991234567',
                'github_url': 'https://github.com/user',
            },
            instance=user,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '+79991234567')

        invalid_form = ProfileForm(
            data={
                'name': 'User',
                'surname': 'One',
                'about': 'Hello',
                'phone': '89991234567',
                'github_url': 'https://gitlab.com/user',
            },
            instance=user,
        )
        self.assertFalse(invalid_form.is_valid())
        self.assertIn('github_url', invalid_form.errors)
