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
from users.models import Classe
import io
from users.models import CustomUser
from collections import defaultdict
import zipfile
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle



User = get_user_model()


@login_required
def export_presences(request):
    if request.user.role != 'secretaire':
        return HttpResponse("Unauthorized", status=403)

    classes = Classe.objects.all()
    selected_classe = None
    start_date = None
    end_date = None
    cours_par_jour = defaultdict(list)

    if 'classe_id' in request.GET and 'start_date' in request.GET and 'end_date' in request.GET:
        classe_id = request.GET.get('classe_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        try:
            selected_classe = Classe.objects.get(id=classe_id)
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (Classe.DoesNotExist, ValueError):
            selected_classe = None

        if selected_classe and start_date and end_date:
            eleves = CustomUser.objects.filter(classe=selected_classe, role="eleve")
            cours_list = Cours.objects.filter(classes=selected_classe,
                                              debut__date__range=[start_date, end_date]).order_by('debut')

            for cours in cours_list:
                # Récupérer les présences avec validation
                presences = Presence.objects.filter(cours=cours, eleve__classe=selected_classe).select_related('eleve')

                presents = [
                    {'eleve': presence.eleve, 'validee_par_prof': presence.validee_par_prof}
                    for presence in presences
                ]

                # Élèves absents (ceux qui n'ont pas de présence enregistrée)
                eleves_present_ids = presences.values_list('eleve_id', flat=True)
                absents = eleves.exclude(id__in=eleves_present_ids)

                # Stockage des informations par jour et par cours
                cours_par_jour[cours.debut.date()].append({
                    'cours': cours,
                    'presents': presents,  # Liste de dicts avec élève + validation
                    'absents': absents
                })

    context = {
        'classes': classes,
        'selected_classe': selected_classe,
        'start_date': start_date,
        'end_date': end_date,
        'cours_par_jour': dict(sorted(cours_par_jour.items())),  # Trie les jours dans l'ordre
    }

    return render(request, 'export_presences.html', context)


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

@login_required
def export_presences_pdf(request):
    if request.user.role != 'secretaire':
        return HttpResponse("Unauthorized", status=403)

    classe_id = request.GET.get('classe_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not classe_id or not start_date_str or not end_date_str:
        return HttpResponse("Paramètres manquants", status=400)

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponse("Date invalide", status=400)

    try:
        selected_classe = Classe.objects.get(id=classe_id)
    except Classe.DoesNotExist:
        return HttpResponse("Classe introuvable", status=404)

    # Récupérer les élèves de la classe sélectionnée
    eleves = CustomUser.objects.filter(classe=selected_classe, role="eleve")

    # Récupérer les cours associés à cette classe sur la période sélectionnée
    cours_list = Cours.objects.filter(classes=selected_classe, debut__date__range=[start_date, end_date]).order_by('debut')

    # Organisation des données par jour
    cours_par_jour = defaultdict(list)
    for cours in cours_list:
        presences = Presence.objects.filter(cours=cours, eleve__classe=selected_classe)
        eleves_present_ids = presences.values_list('eleve_id', flat=True)

        presents = list(CustomUser.objects.filter(id__in=eleves_present_ids, classe=selected_classe))
        absents = eleves.exclude(id__in=eleves_present_ids)

        cours_par_jour[cours.debut.date()].append({
            'cours': cours,
            'presents': presents,
            'absents': absents
        })

    # Création du PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)
    y_position = 750

    p.drawString(100, y_position, f"Présences et absences - Classe : {selected_classe.nom}")
    y_position -= 20
    p.drawString(100, y_position, f"Période : {start_date} - {end_date}")
    y_position -= 30

    for jour, cours_entries in sorted(cours_par_jour.items()):
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, y_position, f"{jour.strftime('%d/%m/%Y')}")
        y_position -= 20

        for entry in cours_entries:
            cours = entry['cours']
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y_position, f"{cours.nom} - {cours.debut.strftime('%H:%M')}")
            y_position -= 20

            p.setFont("Helvetica", 11)
            p.drawString(120, y_position, "Présents :")
            y_position -= 15

            if entry['presents']:
                for eleve in entry['presents']:
                    p.drawString(140, y_position, f"- {eleve.first_name} {eleve.last_name}")
                    y_position -= 15
            else:
                p.drawString(140, y_position, "Aucun élève présent")
                y_position -= 15

            p.drawString(120, y_position, "Absents :")
            y_position -= 15

            if entry['absents']:
                for eleve in entry['absents']:
                    p.drawString(140, y_position, f"- {eleve.first_name} {eleve.last_name}")
                    y_position -= 15
            else:
                p.drawString(140, y_position, "Tous les élèves sont présents")
                y_position -= 15

            y_position -= 10  # Espacement entre les cours

            # Gérer le changement de page si nécessaire
            if y_position < 50:
                p.showPage()
                p.setFont("Helvetica", 12)
                y_position = 750

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="presences_{selected_classe.nom}.pdf"'
    return response

@login_required
def export_presences_par_eleve_pdf(request):
    if request.user.role != 'secretaire':
        return HttpResponse("Unauthorized", status=403)

    classe_id = request.GET.get('classe_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not classe_id or not start_date_str or not end_date_str:
        return HttpResponse("Paramètres manquants", status=400)

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponse("Date invalide", status=400)

    try:
        selected_classe = Classe.objects.get(id=classe_id)
    except Classe.DoesNotExist:
        return HttpResponse("Classe introuvable", status=404)

    # Récupérer les élèves de la classe sélectionnée
    eleves = CustomUser.objects.filter(classe=selected_classe, role="eleve")

    # Récupérer les cours associés à cette classe sur la période sélectionnée
    cours_list = Cours.objects.filter(classes=selected_classe, debut__date__range=[start_date, end_date]).order_by('debut')

    # Organisation des données par élève
    presences_par_eleve = defaultdict(list)
    for cours in cours_list:
        presences = Presence.objects.filter(cours=cours, eleve__classe=selected_classe)
        for eleve in eleves:
            est_present = presences.filter(eleve=eleve).exists()
            presences_par_eleve[eleve].append({
                'cours': cours,
                'present': est_present
            })

    # Création de l'archive ZIP pour stocker les PDFs
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for eleve, cours_entries in presences_par_eleve.items():
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.setFont("Helvetica", 12)
            y_position = 750

            # Titre
            p.drawString(100, y_position, f"Présences et absences - Élève : {eleve.first_name} {eleve.last_name}")
            y_position -= 20
            p.drawString(100, y_position, f"Période : {start_date} - {end_date}")
            y_position -= 30

            # Créer une liste pour le tableau
            table_data = [["Date", "Cours", "Présence"]]

            for entry in cours_entries:
                cours = entry['cours']
                presence_status = "Présent" if entry['present'] else "Absent"
                color = colors.green if entry['present'] else colors.red
                table_data.append([cours.debut.strftime('%d/%m/%Y'), cours.nom, presence_status])

            # Créer le tableau avec Table
            table_data = [["Date", "Cours", "Présence"]]
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ])

            for i, entry in enumerate(cours_entries, start=1):
                cours = entry['cours']
                presence_status = "Présent" if entry['present'] else "Absent"
                presence_color = colors.green if entry['present'] else colors.red
                table_data.append([cours.debut.strftime('%d/%m/%Y'), cours.nom, presence_status])

                # Appliquer la couleur au texte de la colonne "Présence"
                style.add('TEXTCOLOR', (2, i), (2, i), presence_color)

            # Créer le tableau avec les styles corrigés
            table = Table(table_data, colWidths=[100, 300, 100])
            table.setStyle(style)

            table.wrapOn(p, 50, 700)
            table.drawOn(p, 50, y_position - 50)

            p.showPage()
            p.save()

            pdf = buffer.getvalue()
            buffer.close()

            # Ajouter le PDF de chaque élève à l'archive ZIP
            pdf_filename = f"presences_{eleve.first_name}_{eleve.last_name}.pdf"
            zip_file.writestr(pdf_filename, pdf)

    # Retourner l'archive ZIP
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="presences_par_eleve.zip"'
    return response
