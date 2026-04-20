from django.urls import path

from projects import views


app_name = 'projects'

urlpatterns = [
    path('list', views.project_list_view, name='list'),
    path('list/', views.project_list_view, name='list-slash'),
    path('favorites', views.favorite_projects_view, name='favorites-no-slash'),
    path('favorites/', views.favorite_projects_view, name='favorites'),
    path('create-project', views.create_project_view, name='create'),
    path('create-project/', views.create_project_view, name='create-slash'),
    path('<int:project_id>/', views.project_detail_view, name='detail'),
    path('<int:project_id>', views.project_detail_view, name='detail-no-slash'),
    path('<int:project_id>/edit', views.edit_project_view, name='edit'),
    path('<int:project_id>/edit/', views.edit_project_view, name='edit-slash'),
    path('<int:project_id>/complete/', views.complete_project_view, name='complete'),
    path('<int:project_id>/toggle-participate/', views.toggle_participate_view, name='toggle-participate'),
    path('<int:project_id>/toggle-favorite/', views.toggle_favorite_view, name='toggle-favorite'),
]
