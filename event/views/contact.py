from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import CreateView

from event.forms import ContactForm
from event.models import Contact


class ContactView(CreateView):
    template_name = "event/contact.html"
    model = Contact
    form_class = ContactForm
    success_url = reverse_lazy("event:contact")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contact"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Envoyer un email à l'administrateur
        subject = f"Nouveau message de contact: {form.cleaned_data['subject']}"
        message = f"""
        Vous avez reçu un nouveau message de contact:

        Nom: {form.cleaned_data['name']}
        Email: {form.cleaned_data['email']}
        Objet: {form.cleaned_data['subject']}

        Message:
        {form.cleaned_data['message']}

        Date: {self.object.created_at.strftime('%d/%m/%Y %H:%M')}
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],  # Envoyer à l'adresse admin
            fail_silently=False,
        )

        # Envoyer un email de confirmation à l'utilisateur
        confirmation_subject = "Confirmation de votre message - Pro Event"
        confirmation_message = f"""
        Bonjour {form.cleaned_data['name']},

        Nous avons bien reçu votre message et nous vous remercions de nous avoir contacté.
        Nous traiterons votre demande dans les plus brefs délais.

        Récapitulatif de votre message:
        Objet: {form.cleaned_data['subject']}
        Message: {form.cleaned_data['message']}

        L'équipe Pro Event
        """
        send_mail(
            confirmation_subject,
            confirmation_message,
            settings.DEFAULT_FROM_EMAIL,
            [form.cleaned_data["email"]],
            fail_silently=False,
        )

        messages.success(
            self.request,
            "Votre message a été envoyé avec succès! Nous"
            " vous répondrons dans les plus brefs délais.",
        )
        return response
