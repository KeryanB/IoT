from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Classe

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'classe', 'ine', 'is_staff')
    list_filter = ('role', 'classe', 'is_staff', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informations personnelles'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Informations spécifiques'), {'fields': ('role', 'classe', 'ine', 'rfid')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Dates importantes'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'role', 'classe', 'ine', 'rfid'),
        }),
    )

    search_fields = ('username', 'email', 'first_name', 'last_name', 'rfid', 'ine')
    ordering = ('username',)

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)