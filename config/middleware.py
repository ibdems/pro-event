from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils.timezone import now


class SessionTimeoutMiddleware:
    """
    Middleware pour verrouiller la session après une période d'inactivité.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignorer les utilisateurs qui ne sont pas connectés
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Récupérer le namespace de l'URL actuelle
        current_namespace = resolve(request.path_info).namespace

        # Exclure toutes les URLs de l'application 'event' et les URLs spécifiques
        excluded_namespaces = ["event"]  # Ajouter d'autres namespaces si nécessaire
        excluded_urls = [
            reverse("lock"),
            reverse("password_reset"),
            reverse("password_reset_done"),
            reverse("password_reset_complete"),
        ]

        # Si l'URL appartient à un namespace exclu ou fait partie des URLs spécifiques, ignorer
        if current_namespace in excluded_namespaces or request.path in excluded_urls:
            return self.get_response(request)

        # Durée maximale d'inactivité avant verrouillage (en secondes)
        timeout_seconds = 500

        # Vérifier la dernière activité
        last_activity = request.session.get("last_activity")

        if last_activity:
            elapsed_time = now().timestamp() - last_activity

            # Si le temps écoulé dépasse le délai, rediriger vers la page de verrouillage
            if elapsed_time > timeout_seconds:
                request.session["locked"] = True
                return redirect("lock")

        # Mettre à jour la dernière activité si la session n'est pas verrouillée
        if not request.session.get("locked"):
            request.session["last_activity"] = now().timestamp()

        return self.get_response(request)
