from django.db import models
from django.conf import settings
from cours.models import Cours

class Presence(models.Model):
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'eleve'})
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    heure_arrivee = models.TimeField(auto_now_add=True)
    validee_par_prof = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.eleve} - {self.cours} - {self.date}"
