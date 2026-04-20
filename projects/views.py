import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from projects.forms import ProjectForm
from projects.models import Project
from users.models import Skill


def home_redirect(request):
    return redirect('/projects/list')


def project_list_view(request):
    projects = Project.objects.select_related('owner').prefetch_related('participants', 'skills').all()
    context = {}
    task_version = getattr(settings, 'TASK_VERSION', '1')

    if task_version == '3':
        all_skills = Skill.objects.order_by('name')
        active_skill = request.GET.get('skill')
        if active_skill:
            projects = projects.filter(skills__name=active_skill)
        context.update({'all_skills': all_skills, 'active_skill': active_skill})

    paginator = Paginator(projects.distinct().order_by('-created_at', '-id'), 12)
    page = paginator.get_page(request.GET.get('page'))
    context['projects'] = page
    return render(request, 'projects/project_list.html', context)


def favorite_projects_view(request):
    if getattr(settings, 'TASK_VERSION', '1') != '1':
        raise Http404
    if not request.user.is_authenticated:
        return redirect('/users/login/')
    projects = Project.objects.filter(interested_users=request.user).select_related('owner').prefetch_related('participants')
    paginator = Paginator(projects.order_by('-created_at', '-id'), 12)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'projects/favorite_projects.html', {'projects': page})


def project_detail_view(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related('owner').prefetch_related('participants', 'skills'),
        pk=project_id,
    )
    return render(request, 'projects/project-details.html', {'project': project})


@login_required
@require_http_methods(['GET', 'POST'])
def create_project_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect(f'/projects/{project.id}')
    else:
        form = ProjectForm(initial={'status': Project.STATUS_OPEN})
    return render(request, 'projects/create-project.html', {'form': form, 'is_edit': False})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_project_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user != project.owner and not request.user.is_staff:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            return redirect(f'/projects/{project.id}')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/create-project.html', {'form': form, 'is_edit': True})


@login_required
@require_POST
def complete_project_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user != project.owner and not request.user.is_staff:
        return JsonResponse({'status': 'error'}, status=403)
    if project.status != Project.STATUS_OPEN:
        return JsonResponse({'status': 'error'}, status=400)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=['status'])
    return JsonResponse({'status': 'ok', 'project_status': 'closed'})


@login_required
@require_POST
def toggle_participate_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({'status': 'ok', 'participant': participant})


@login_required
@require_POST
def toggle_favorite_view(request, project_id):
    if getattr(settings, 'TASK_VERSION', '1') != '1':
        raise Http404
    project = get_object_or_404(Project, pk=project_id)
    favorited = not project.interested_users.filter(pk=request.user.pk).exists()
    if favorited:
        project.interested_users.add(request.user)
    else:
        project.interested_users.remove(request.user)
    return JsonResponse({'status': 'ok', 'favorited': favorited})


@require_GET
def skills_autocomplete_view(request):
    if getattr(settings, 'TASK_VERSION', '1') != '3':
        raise Http404
    q = request.GET.get('q', '').strip()
    queryset = Skill.objects.all()
    if q:
        queryset = queryset.filter(name__istartswith=q)
    return JsonResponse(list(queryset.order_by('name').values('id', 'name')[:10]), safe=False)


@login_required
@require_POST
def add_skill_to_project_view(request, project_id):
    if getattr(settings, 'TASK_VERSION', '1') != '3':
        raise Http404
    project = get_object_or_404(Project, pk=project_id)
    if request.user != project.owner and not request.user.is_staff:
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

    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)

    return JsonResponse(
        {'id': skill.id, 'name': skill.name, 'skill_id': skill.id, 'created': created, 'added': added}
    )


@login_required
@require_POST
def remove_skill_from_project_view(request, project_id, skill_id):
    if getattr(settings, 'TASK_VERSION', '1') != '3':
        raise Http404
    project = get_object_or_404(Project, pk=project_id)
    if request.user != project.owner and not request.user.is_staff:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse({'detail': 'skill not found in project'}, status=400)
    project.skills.remove(skill)
    return JsonResponse({'status': 'ok'})


def parse_json(request):
    if request.body:
        try:
            return json.loads(request.body.decode('utf-8'))
        except (TypeError, ValueError):
            return {}
    return {}
