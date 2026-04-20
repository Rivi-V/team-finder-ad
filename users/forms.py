import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from users.models import User

PHONE_PATTERN = re.compile(r'^(8\d{10}|\+7\d{10})$')


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')

    class Meta:
        model = User
        fields = ('name', 'surname', 'email', 'password')

    def save(self, commit=True):
        user = User(
            name=self.cleaned_data['name'],
            surname=self.cleaned_data['surname'],
            email=self.cleaned_data['email'],
        )
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Неверный имейл или пароль')
        return cleaned_data

    def get_user(self):
        return self.user_cache


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'surname', 'avatar', 'about', 'phone', 'github_url')

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            return ''
        if not PHONE_PATTERN.fullmatch(phone):
            raise forms.ValidationError('Введите телефон в формате 8XXXXXXXXXX или +7XXXXXXXXXX')

        normalized = '+7' + phone[1:] if phone.startswith('8') else phone
        alt = '8' + normalized[2:]
        exists = User.objects.exclude(pk=self.instance.pk).filter(phone__in=[phone, normalized, alt]).exists()
        if exists:
            raise forms.ValidationError('Этот номер телефона уже используется')
        return normalized

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


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput, label='Старый пароль')
    new_password1 = forms.CharField(widget=forms.PasswordInput, label='Новый пароль')
    new_password2 = forms.CharField(widget=forms.PasswordInput, label='Повторите пароль')
