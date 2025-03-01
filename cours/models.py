from django.db import models
from django.conf import settings

class Cours(models.Model):
    nom = models.CharField(max_length=100)
    professeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'prof'})
    debut = models.DateTimeField()
    fin = models.DateTimeField()
    classes = models.ManyToManyField('users.Classe', related_name='cours')

    def __str__(self):
        return f"{self.nom} ({self.professeur})"
