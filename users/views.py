import json

from django.conf import settings
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from users.forms import LoginForm, ProfileForm, RegisterForm, UserPasswordChangeForm
from users.models import Skill, User


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
    participants = User.objects.prefetch_related('skills').all()
    context = {}
    task_version = getattr(settings, 'TASK_VERSION', '1')

    if task_version == '1' and request.user.is_authenticated:
        active_filter = request.GET.get('filter')
        context['active_filter'] = active_filter
        participants = apply_variant_one_filter(participants, request.user, active_filter)
    elif task_version == '2':
        all_skills = Skill.objects.order_by('name')
        active_skill = request.GET.get('skill')
        if active_skill:
            participants = participants.filter(skills__name=active_skill)
        context.update({'all_skills': all_skills, 'active_skill': active_skill})

    paginator = Paginator(participants.distinct().order_by('-date_joined', '-id'), 12)
    page = paginator.get_page(request.GET.get('page'))
    context['participants'] = page
    return render(request, 'users/participants.html', context)


@require_GET
def skills_autocomplete_view(request):
    if getattr(settings, 'TASK_VERSION', '1') != '2':
        raise Http404
    q = request.GET.get('q', '').strip()
    queryset = Skill.objects.all()
    if q:
        queryset = queryset.filter(name__istartswith=q)
    data = list(queryset.order_by('name').values('id', 'name')[:10])
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def add_skill_to_user_view(request, user_id):
    if getattr(settings, 'TASK_VERSION', '1') != '2':
        raise Http404
    if request.user.id != user_id and not request.user.is_staff:
        return JsonResponse({'detail': 'forbidden'}, status=403)

    payload = parse_json(request)
    skill_id = payload.get('skill_id')
    name = (payload.get('name') or '').strip()

    created = False
    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse({'detail': 'skill_id or name required'}, status=400)

    target_user = request.user if request.user.id == user_id else get_object_or_404(User, pk=user_id)
    added = not target_user.skills.filter(pk=skill.pk).exists()
    if added:
        target_user.skills.add(skill)

    return JsonResponse(
        {'id': skill.id, 'name': skill.name, 'skill_id': skill.id, 'created': created, 'added': added}
    )


@login_required
@require_POST
def remove_skill_from_user_view(request, user_id, skill_id):
    if getattr(settings, 'TASK_VERSION', '1') != '2':
        raise Http404
    if request.user.id != user_id and not request.user.is_staff:
        return JsonResponse({'detail': 'forbidden'}, status=403)

    target_user = request.user if request.user.id == user_id else get_object_or_404(User, pk=user_id)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not target_user.skills.filter(pk=skill.pk).exists():
        return JsonResponse({'detail': 'skill not found in profile'}, status=400)

    target_user.skills.remove(skill)
    return JsonResponse({'status': 'ok'})


def parse_json(request):
    if request.body:
        try:
            return json.loads(request.body.decode('utf-8'))
        except (TypeError, ValueError):
            return {}
    return {}


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
