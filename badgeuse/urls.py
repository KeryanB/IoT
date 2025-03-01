"""
URL configuration for badgeuse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# badgeuse/urls.py
from django.contrib import admin
from django.urls import path
from presence.views import list_presences, filter_prof_cours, filter_presences, export_presences, export_presences_pdf, export_presences_par_eleve_pdf, filter_presences_2
from .views import dashboard
from django.contrib.auth import views as auth_views  # Importer la vue LoginView
from users.views import profile, users_list, add_user, edit_user, delete_user
from django.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('list/', list_presences, name='list_presences'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),  # Ajout de la route pour la connexion
    path('export_presences/', export_presences, name='export_presences'),
    path('accounts/profile/<int:user_id>/', profile, name='profile'),
    path('', dashboard, name='dashboard'),
    path('users_list', users_list, name='users_list'),
    path("add_user", add_user, name="add_user"),
    path("edit_user/<int:user_id>/", edit_user, name="edit_user"),
    path("delete_user/<int:user_id>/", delete_user, name="delete_user"),
    path('export_presences/', export_presences, name='export_presences'),
    path('filter_presences/', filter_presences, name='filter_presences'),
    path('filter_presences_2/', filter_presences_2, name='filter_presences_2'),
    path('filter_prof_cours/', filter_prof_cours, name='filter_prof_cours'),
    path('export_presences_pdf/', export_presences_pdf, name='export_presences_pdf'),
    path('export_presences_par_eleve_pdf/', export_presences_par_eleve_pdf, name='export_presences_par_eleve_pdf'),
]
