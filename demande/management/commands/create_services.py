from django.core.management.base import BaseCommand
from django.db import transaction

from demande.models import Service


class Command(BaseCommand):
    help = "Crée les services de base pour l'application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime tous les services existants avant d'en créer de nouveaux",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Service.objects.all().delete()
            self.stdout.write(self.style.WARNING("Tous les services existants ont été supprimés."))

        # Définition des services
        services = [
            {
                "name": "Organisation d'événements",
                "description": "Service d'organisation et de gestion complète d'événements (conférences, séminaires, galas, etc.)",  # noqa
                "accronyme": "event",
            },
            {
                "name": "Billetterie",
                "description": "Service de création et de gestion de tickets pour vos événements avec contrôle d'accès",  # noqa
                "accronyme": "ticket",
            },
            {
                "name": "Service d'hôtesses",
                "description": "Mise à disposition d'hôtesses professionnelles pour l'accueil de vos invités et la gestion de votre événement",  # noqa
                "accronyme": "hostess",
            },
        ]

        # Création des services
        created_count = 0
        updated_count = 0

        for service_data in services:
            service, created = Service.objects.update_or_create(
                accronyme=service_data["accronyme"],
                defaults={"name": service_data["name"], "description": service_data["description"]},
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Service '{service.name}' ({service.accronyme}) créé avec succès."
                    )
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Service '{service.name}' ({service.accronyme}) mis à jour."
                    )
                )
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Opération terminée : {created_count} services créés, {updated_count} services mis à jour."  # noqa
            )
        )
