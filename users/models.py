from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class Classe(models.Model):
    nom = models.CharField(max_length=100, unique=True)  # Nom de la classe (ex: "Mathématiques 101")

    def __str__(self):
        return self.nom
class CustomUser(AbstractUser):
    ROLES = [
        ('admin', 'Admin'),
        ('prof', 'Prof'),
        ('secretaire', 'Secrétaire'),
        ('eleve', 'Élève'),
    ]
    role = models.CharField(max_length=20, choices=ROLES)
    ine = models.CharField(max_length=15, blank=True, null=True)
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True, help_text="Applicable uniquement si le rôle est Élève")
    rfid = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

