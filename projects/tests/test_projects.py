import tempfile
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings

from projects.models import Project
from users.models import Skill, User

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
class ProjectCoreTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='password', name='Owner', surname='User'
        )
        self.member = User.objects.create_user(
            email='member@example.com', password='password', name='Member', surname='User'
        )

    def test_project_create_adds_owner_to_participants(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            '/projects/create-project/',
            {
                'name': 'New Project',
                'description': 'Description',
                'github_url': 'https://github.com/example/new-project',
                'status': Project.STATUS_OPEN,
            },
        )
        project = Project.objects.get(name='New Project')
        self.assertRedirects(response, f'/projects/{project.id}')
        self.assertEqual(project.owner, self.owner)
        self.assertTrue(project.participants.filter(pk=self.owner.pk).exists())

    def test_favorites_participation_and_pagination(self):
        project = Project.objects.create(name='Pet', description='Desc', owner=self.owner)
        project.participants.add(self.owner)

        self.client.force_login(self.member)
        fav_resp = self.client.post(f'/projects/{project.id}/toggle-favorite/')
        self.assertEqual(fav_resp.json()['favorited'], True)

        participate_resp = self.client.post(f'/projects/{project.id}/toggle-participate/')
        self.assertEqual(participate_resp.json()['participant'], True)

        favorites_page = self.client.get('/projects/favorites/')
        self.assertContains(favorites_page, 'Pet')

        participants_page = self.client.get('/users/list/?filter=owners-of-favorite-projects')
        participants = list(participants_page.context['participants'])
        self.assertEqual(participants, [self.owner])

        for idx in range(13):
            Project.objects.create(name=f'Project {idx}', owner=self.owner)
        response = self.client.get('/projects/list/')
        self.assertEqual(response.context['projects'].paginator.num_pages, 2)

    def test_complete_project(self):
        project = Project.objects.create(name='Closable', owner=self.owner)
        self.client.force_login(self.owner)
        response = self.client.post(f'/projects/{project.id}/complete/')
        project.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.status, Project.STATUS_CLOSED)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, TASK_VERSION='3', TEMPLATES=variant_templates('3'))
class VariantThreeSkillTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner3@example.com', password='password', name='Owner', surname='Three'
        )
        self.project = Project.objects.create(name='Skillful', owner=self.owner)
        self.client.force_login(self.owner)

    def test_add_remove_and_filter_project_skills(self):
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            data='{"name": "Python"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        skill = Skill.objects.get(name='Python')
        self.assertTrue(self.project.skills.filter(pk=skill.pk).exists())

        autocomplete = self.client.get('/projects/skills/?q=Pyt')
        self.assertEqual(autocomplete.status_code, 200)
        self.assertEqual(autocomplete.json()[0]['name'], 'Python')

        response = self.client.get('/projects/list/?skill=Python')
        self.assertContains(response, 'Skillful')

        remove_response = self.client.post(f'/projects/{self.project.id}/skills/{skill.id}/remove/')
        self.assertEqual(remove_response.status_code, 200)
        self.assertFalse(self.project.skills.filter(pk=skill.pk).exists())
