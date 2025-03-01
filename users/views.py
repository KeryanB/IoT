from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .decorators import admin_required, prof_required, secretaire_required, staff_required, secretaire_or_admin_required
from users.models import CustomUser, Classe
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden

@login_required
def profile(request, user_id):
    # Récupère l'utilisateur correspondant à l'ID donné
    profil_utilisateur = get_object_or_404(CustomUser, id=user_id)

    # Vérifie si l'utilisateur connecté peut voir le profil demandé
    if profil_utilisateur != request.user:
        # Vérifie si l'utilisateur a les droits d'accès
        if (request.user.role not in ['admin', 'prof', 'secretaire']) and not request.user.is_superuser:
            return HttpResponseForbidden("Vous n'avez pas l'autorisation de voir ce profil.")

    return render(request, 'profile.html', {'profil_utilisateur': profil_utilisateur})

@login_required
@staff_required
def users_list(request):
    users = CustomUser.objects.all()
    classes = Classe.objects.all()
    roles = CustomUser.ROLES
    return render(request, 'users_list.html', {'users': users,"classes": classes, "roles": roles})

@login_required
@secretaire_or_admin_required
def add_user(request):
    classes = Classe.objects.all()  # Récupère toutes les classes

    if request.method == "POST":
        classe_id = request.POST.get("classe", None)
        email = request.POST["email"]
        password = request.POST["password"]
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        ine = request.POST.get("ine", "")
        role = request.POST["role"]

        # Vérifie si l'utilisateur existe déjà
        if CustomUser.objects.filter(ine=ine).exists():
            messages.error(request, "Cet INE est déjà pris.")
            return redirect("users_list")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect("users_list")

        classe_id = request.POST.get("classe", None)  # Récupérer la valeur ou None

        # Vérifier si la classe existe uniquement si un ID a été fourni
        classe = None
        if classe_id:
            try:
                classe = Classe.objects.get(id=classe_id)
            except Classe.DoesNotExist:
                messages.error(request, "Classe invalide.")
                return redirect("users_list")

        # Si le rôle ne nécessite pas de classe, la valeur est ignorée
        if role in ["admin", "prof", "secretaire"]:
            classe = None

        # Création de l'utilisateur
        new_user = CustomUser(
            username=ine,
            classe=classe,  # Stocke l'objet Classe et non un string
            email=email,
            first_name=first_name,
            last_name=last_name,
            ine=ine,
            role=role,
            password=make_password(password)  # Hash du mot de passe
        )
        new_user.save()
        messages.success(request, "Utilisateur ajouté avec succès !")
        return redirect("users_list")

    return render(request, "users_list.html", {"classes": classes})  # Passe les classes au template

@login_required
@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "Utilisateur supprimé !")
    return redirect("users_list")

@login_required
@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        user.username = request.POST["username"]
        user.email = request.POST["email"]
        user.role = request.POST["role"]
        user.first_name = request.POST["first_name"]
        user.last_name = request.POST["last_name"]
        user.ine = request.POST["ine"]
        user.save()
        messages.success(request, "Utilisateur mis à jour !")
        return redirect("users_list")

    return render(request, "edit_user.html", {"user": user})
