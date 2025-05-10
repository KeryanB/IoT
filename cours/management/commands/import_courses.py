import requests
from icalendar import Calendar
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cours.models import Cours
from users.models import Classe
from django.contrib.auth.hashers import make_password


User = get_user_model()  # Utilisation du modèle CustomUser

class Command(BaseCommand):
    help = "Importe les cours depuis l'URL iCal pour toutes les classes"

    def handle(self, *args, **kwargs):
        today = date.today()  # Date du jour
        classes = Classe.objects.exclude(url_ical="")  # Sélection des classes avec une URL iCal

        if not classes.exists():
            self.stdout.write(self.style.ERROR("Aucune classe avec une URL iCal trouvée."))
            return

        for classe in classes:
            self.stdout.write(f"📅 Importation des cours pour {classe.nom}...")
            self.import_courses_for_class(classe, today)

    def import_courses_for_class(self, classe, target_date):
        """
        Télécharge le calendrier iCal et ajoute les cours pour une classe donnée.
        Si le nom du cours contient 'Gr1' ou 'Gr2', le cours est associé uniquement à la classe
        correspondante. S'il n'y a pas d'indication de groupe, le cours est ajouté à toutes les classes.
        """
        try:
            response = requests.get(classe.url_ical)
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"❌ Erreur {response.status_code} en récupérant {classe.url_ical}"))
                return

            cal = Calendar.from_ical(response.content)
            events_found = False

            for component in cal.walk():
                if component.name == "VEVENT":
                    start = component.get('dtstart').dt
                    end = component.get('dtend').dt

                    start_date = start.date() if isinstance(start, datetime) else start
                    if start_date == target_date:
                        events_found = True
                        summary = component.get('summary')
                        location = component.get('location', "Non spécifié")
                        description = component.get('description', "")

                        # Détermination du groupe indiqué dans le nom du cours (s'il existe)
                        group_assigned = None
                        if "Gr1" in summary:
                            group_assigned = "Gr1"
                        elif "Gr2" in summary:
                            group_assigned = "Gr2"

                        prof_name = self.extract_professor_name(description)
                        professeur = self.get_or_create_professor(prof_name)

                        # Vérifier si un cours avec le même nom, prof et horaires existe déjà
                        cours_obj, created = Cours.objects.get_or_create(
                            nom=summary,
                            debut=start,
                            fin=end,
                            professeur=professeur,
                        )

                        # Associer la classe au cours selon le groupe indiqué :
                        if group_assigned:
                            # Si le nom du groupe est indiqué, on ajoute uniquement si la classe correspond
                            if group_assigned in classe.nom:
                                if not cours_obj.classes.filter(id=classe.id).exists():
                                    cours_obj.classes.add(classe)
                                    self.stdout.write(self.style.SUCCESS(f"✅ {classe.nom} ajouté à {summary}"))
                        else:
                            # Pas d'indication de groupe, on ajoute la classe (les deux groupes seront traités)
                            if not cours_obj.classes.filter(id=classe.id).exists():
                                cours_obj.classes.add(classe)
                                self.stdout.write(self.style.SUCCESS(f"✅ {classe.nom} ajouté à {summary}"))

            if not events_found:
                self.stdout.write(self.style.WARNING(f"⚠️ Aucun cours trouvé pour {target_date}."))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur de connexion : {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur d'importation : {e}"))

    def extract_professor_name(self, description):
        """
        Extrait le nom du professeur à partir de la description du cours.
        """
        lines = [line.strip() for line in description.split("\n") if line.strip()]
        return lines[1] if len(lines) >= 2 else "Professeur Inconnu"

    def get_or_create_professor(self, name):
        """
        Recherche un professeur existant ou le crée si nécessaire.
        Le username sera en Prenom_Nom (tous les espaces remplacés par des '_').
        """
        if name == "Professeur Inconnu":
            return None

        # Transformation de "Prénom Nom" (ou "Nom Prénom") en "Prénom_Nom"
        username = name.replace(" ", "_")

        # Extraction nom / prénom pour les autres champs
        parts = name.split()
        nom = parts[-1]             # dernier token comme nom
        prenom = " ".join(parts[:-1])  # tout le reste comme prénom
        email = f"{prenom.lower()}.{nom.lower()}@insa-strasbourg.fr"

        # Mot de passe : prenom+nom+date_du_jour
        today_str = date.today().strftime('%d%m%Y')
        password = f"{prenom.lower()}{nom.lower()}{today_str}"

        professeur, created = User.objects.get_or_create(
            username=username,
            defaults={
                "role": "prof",
                "password": make_password(password),
                "first_name": prenom,
                "last_name": nom,
                "email": email,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"👨‍🏫 Professeur créé : {username}"))

        return professeur
