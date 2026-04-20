from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from projects.forms import ProjectForm
from projects.models import Project


def home_redirect(request):
    return redirect('/projects/list')


def project_list_view(request):
    projects = Project.objects.select_related('owner').prefetch_related('participants').all()
    paginator = Paginator(projects.distinct().order_by('-created_at', '-id'), 12)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'projects/project_list.html', {'projects': page})


def favorite_projects_view(request):
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
    project = get_object_or_404(Project, pk=project_id)
    favorited = not project.interested_users.filter(pk=request.user.pk).exists()
    if favorited:
        project.interested_users.add(request.user)
    else:
        project.interested_users.remove(request.user)
    return JsonResponse({'status': 'ok', 'favorited': favorited})
