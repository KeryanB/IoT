# dans badgeuse/presence/views.py
from django.http import HttpResponse, JsonResponse
from .models import Presence  # Assure-toi que tu as un modèle Presence
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils import timezone
from cours.models import Cours
from datetime import datetime
from django.contrib.auth import get_user_model

User = get_user_model()


def export_presences(request):
    # Création du fichier PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="presences.pdf"'

    # Création d'un objet canvas pour générer le PDF
    p = canvas.Canvas(response, pagesize=letter)

    # Ajouter le contenu du PDF (ici, un simple exemple)
    p.drawString(100, 750, "Liste des présences")
    presences = Presence.objects.all()  # Récupère toutes les présences
    y_position = 730
    for presence in presences:
        p.drawString(100, y_position, f"{presence.nom} - {presence.prenom} - {presence.date}")
        y_position -= 20

    p.showPage()
    p.save()

    return response

@login_required
def list_presences(request):
    today = timezone.now().date()
    presences = Presence.objects.filter(eleve=request.user).order_by('-date')
    return render(request, 'list.html', {'presences': presences, "today": today})

@login_required
def filter_presences(request):
    """
    Filtre pour les élèves :
    - Récupère les cours de la journée associés à la classe de l'élève.
    - Récupère les présences de l'élève pour la date sélectionnée.
    - Déduit les cours auxquels l'élève était absent.
    Renvoie le partial 'partials/presences_list.html'.
    """
    user = request.user
    selected_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))

    if user.classe:
        # Ici, Cours possède un ManyToManyField nommé 'classes' reliant aux instances de Classe.
        cours_du_jour = Cours.objects.filter(debut__date=selected_date, classes=user.classe)
    else:
        cours_du_jour = Cours.objects.none()

    presences = Presence.objects.filter(eleve=user, cours__debut__date=selected_date)
    cours_absents = cours_du_jour.exclude(id__in=presences.values_list('cours_id', flat=True))

    return render(request, 'partials/presences_list.html', {
        'presences': presences,
        'cours_absents': cours_absents,
        'selected_date': selected_date
    })


@login_required
def filter_prof_cours(request):
    """
    Pour les professeurs : récupère les cours du jour et, pour chaque cours,
    calcule l'ensemble des absences en unissant tous les élèves inscrits
    dans toutes les classes associées et en excluant ceux qui ont une présence enregistrée.
    Renvoie le template fusionné 'merged_prof_view.html'.
    """
    user = request.user
    selected_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    cours_list = Cours.objects.filter(professeur=user, debut__date=selected_date)

    for cours in cours_list:
        # Union de tous les élèves inscrits dans toutes les classes associées au cours
        eleves_inscrits = User.objects.none()
        for classe in cours.classes.all():
            eleves_inscrits = eleves_inscrits | classe.customuser_set.all()
        eleves_inscrits = eleves_inscrits.distinct()

        # Récupérer les présences pour ce cours
        presences = Presence.objects.filter(cours=cours)
        eleves_present_ids = presences.values_list('eleve_id', flat=True)

        # Calculer les absents
        absents = eleves_inscrits.exclude(id__in=eleves_present_ids)
        # Affecter la liste des absents à l'attribut 'absences' du cours
        cours.absences = absents

    return render(request, 'partials/professeur_cours_list.html', {
        'cours_list': cours_list,
        'selected_date': selected_date,
    })
