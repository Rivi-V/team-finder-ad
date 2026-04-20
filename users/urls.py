app_name = 'users'

from django.urls import path

from users import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('list', views.users_list_view, name='list'),
    path('list/', views.users_list_view, name='list-slash'),
    path('edit-profile', views.edit_profile_view, name='edit-profile'),
    path('edit-profile/', views.edit_profile_view, name='edit-profile-slash'),
    path('change-password', views.change_password_view, name='change-password'),
    path('change-password/', views.change_password_view, name='change-password-slash'),
    path('skills/', views.skills_autocomplete_view, name='skills-autocomplete'),
    path('<int:user_id>', views.user_detail_view, name='detail-no-slash'),
    path('<int:user_id>/', views.user_detail_view, name='detail'),
    path('<int:user_id>/skills/add/', views.add_skill_to_user_view, name='skill-add'),
    path('<int:user_id>/skills/<int:skill_id>/remove/', views.remove_skill_from_user_view, name='skill-remove'),
]
