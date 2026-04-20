from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from users.forms import LoginForm, ProfileForm, RegisterForm, UserPasswordChangeForm
from users.models import User


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/users/login/')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('/projects/list')
    else:
        form = LoginForm(request)
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/projects/list')


def user_detail_view(request, user_id):
    profile_user = get_object_or_404(
        User.objects.prefetch_related('owned_projects__participants', 'skills'),
        pk=user_id,
    )
    return render(request, 'users/user-details.html', {'user': profile_user})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(f'/users/{request.user.id}')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def change_password_view(request):
    if request.method == 'POST':
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(f'/users/{request.user.id}')
    else:
        form = UserPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})


def users_list_view(request):
    participants = User.objects.all()
    context = {}
    if request.user.is_authenticated:
        active_filter = request.GET.get('filter')
        context['active_filter'] = active_filter
        participants = apply_variant_one_filter(participants, request.user, active_filter)

    paginator = Paginator(participants.distinct().order_by('-date_joined', '-id'), 12)
    page = paginator.get_page(request.GET.get('page'))
    context['participants'] = page
    return render(request, 'users/participants.html', context)


def apply_variant_one_filter(queryset, current_user, active_filter):
    if active_filter == 'owners-of-favorite-projects':
        return queryset.filter(owned_projects__interested_users=current_user)
    if active_filter == 'owners-of-participating-projects':
        return queryset.filter(owned_projects__participants=current_user)
    if active_filter == 'interested-in-my-projects':
        return queryset.filter(favorites__owner=current_user)
    if active_filter == 'participants-of-my-projects':
        return queryset.filter(participated_projects__owner=current_user)
    return queryset
