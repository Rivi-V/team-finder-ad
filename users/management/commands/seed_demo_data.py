from django.core.management.base import BaseCommand

from projects.models import Project
from users.models import Skill, User


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей и проекты для TeamFinder.'

    def handle(self, *args, **options):
        users_data = [
            {
                'email': 'maria@yandex.ru',
                'password': 'password',
                'name': 'Мария',
                'surname': 'Иванова',
                'about': 'Backend-разработчик, люблю pet-проекты и Python.',
                'phone': '+79990000001',
                'github_url': 'https://github.com/maria',
            },
            {
                'email': 'alex@example.com',
                'password': 'password',
                'name': 'Алексей',
                'surname': 'Смирнов',
                'about': 'Frontend-разработчик, работаю с React и TypeScript.',
                'phone': '+79990000002',
                'github_url': 'https://github.com/alex',
            },
            {
                'email': 'olga@example.com',
                'password': 'password',
                'name': 'Ольга',
                'surname': 'Петрова',
                'about': 'Дизайнер интерфейсов, люблю исследовать новые идеи.',
                'phone': '+79990000003',
                'github_url': 'https://github.com/olga',
            },
        ]

        created_users = []
        for item in users_data:
            user, created = User.objects.get_or_create(
                email=item['email'],
                defaults={
                    'name': item['name'],
                    'surname': item['surname'],
                    'about': item['about'],
                    'phone': item['phone'],
                    'github_url': item['github_url'],
                },
            )
            if created:
                user.set_password(item['password'])
                user.save()
            created_users.append(user)

        skill_python, _ = Skill.objects.get_or_create(name='Python')
        skill_django, _ = Skill.objects.get_or_create(name='Django')
        skill_react, _ = Skill.objects.get_or_create(name='React')
        skill_figma, _ = Skill.objects.get_or_create(name='Figma')

        maria, alex, olga = created_users
        maria.skills.add(skill_python, skill_django)
        alex.skills.add(skill_react)
        olga.skills.add(skill_figma)

        projects_data = [
            {
                'owner': maria,
                'name': 'Task Tracker',
                'description': 'Простой трекер задач для маленькой продуктовой команды.',
                'github_url': 'https://github.com/maria/task-tracker',
                'skills': [skill_python, skill_django],
                'participants': [maria, alex],
            },
            {
                'owner': alex,
                'name': 'UI Kit Showcase',
                'description': 'Каталог UI-компонентов для pet-проектов.',
                'github_url': 'https://github.com/alex/ui-kit-showcase',
                'skills': [skill_react, skill_figma],
                'participants': [alex, olga],
            },
            {
                'owner': olga,
                'name': 'Portfolio Builder',
                'description': 'Конструктор личного портфолио для начинающих специалистов.',
                'github_url': 'https://github.com/olga/portfolio-builder',
                'skills': [skill_figma, skill_python],
                'participants': [olga, maria],
            },
        ]

        for item in projects_data:
            project, _ = Project.objects.get_or_create(
                owner=item['owner'],
                name=item['name'],
                defaults={
                    'description': item['description'],
                    'github_url': item['github_url'],
                    'status': Project.STATUS_OPEN,
                },
            )
            project.skills.add(*item['skills'])
            project.participants.add(*item['participants'])

        self.stdout.write(self.style.SUCCESS('Тестовые данные TeamFinder готовы.'))
