from django.http import HttpResponseForbidden

def admin_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_staff or request.user.role == 'admin' or request.user.is_superuser:  # Vérifie si l'utilisateur est admin
            return function(request, *args, **kwargs)
        return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette page.")
    return wrap

def prof_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.role != 'prof':  # Vérifie si l'utilisateur est professeur
            return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette page.")
        return function(request, *args, **kwargs)
    return wrap

def secretaire_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.role != 'secretaire':  # Vérifie si l'utilisateur est secrétaire
            return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette page.")
        return function(request, *args, **kwargs)
    return wrap

def staff_required(function):
    def wrap(request, *args, **kwargs):
        # Vérifie si l'utilisateur est admin, prof, ou secrétaire
        if not (request.user.is_staff or request.user.role in ['prof', 'secretaire', 'admin']):
            return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette page.")
        return function(request, *args, **kwargs)
    return wrap

def secretaire_or_admin_required(function):
    def wrap(request, *args, **kwargs):
        # Vérifie si l'utilisateur est admin, prof, ou secrétaire
        if not (request.user.is_staff or request.user.role in ['secretaire', 'admin']):
            return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette page.")
        return function(request, *args, **kwargs)
    return wrap