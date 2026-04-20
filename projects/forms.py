from urllib.parse import urlparse

from django import forms

from projects.models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description', 'github_url', 'status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].label = 'Статус'
        self.fields['status'].choices = (
            (Project.STATUS_OPEN, 'Открыт'),
            (Project.STATUS_CLOSED, 'Закрыт'),
        )

    def clean_github_url(self):
        url = (self.cleaned_data.get('github_url') or '').strip()
        if not url:
            return ''
        host = urlparse(url).netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
        if host != 'github.com':
            raise forms.ValidationError('Ссылка должна вести на GitHub')
        return url
