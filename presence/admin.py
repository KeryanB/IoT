from django.contrib import admin
from .models import Presence  # Assure-toi d'importer Presence et non "presence"

admin.site.register(Presence)
