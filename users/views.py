from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView, PasswordResetView,PasswordResetConfirmView
from django.utils.http import urlsafe_base64_decode
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.tokens import default_token_generator
from .utils.send_emails import send_mail_activation, send_mail_reset_password
from users.models import User
from .forms import CustomCreateUserForm, CustomLoginForm
from django.views.generic import CreateView
from django.contrib import messages
from django.db import transaction

class CustomLoginView(LoginView):
    form_class =CustomLoginForm

class CustomUserCreationView(CreateView):
    template_name = 'registration/register.html'
    form_class = CustomCreateUserForm
    success_url = reverse_lazy('register')

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_mail_activation(user)
        messages.success(
            self.request,
            ("Votre compte compte a ete cree")
        )
        return redirect(self.success_url)


class ActivationUserView(View):
    login_url = reverse_lazy('login')

    def get(self, request, uid, token):
        id = urlsafe_base64_decode(uid)

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return render(request, 'registration/activation_invalid.html')
        
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()

            messages.success(
                self.request, "Votre a ete activer vous pouvez vous connectez"
            )
            return redirect(self.login_url)
        return render (request, 'registration/activation_invalid.html')

class PasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    post_reset_redirect = 'password_confirmation'
    
    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            send_mail_reset_password(user)
            messages.success(self.request, "Vous avez recu un email de confirmation, Veuillez consulter votre boite mail")
        else:
            messages.error(self.request, "Cet email n'est associé à aucun utilisateur.")
         
        return render(self.request, 'registration/password_reset.html')
    

class CustomPasswordConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_confirm.html'
    success_url = reverse_lazy('login')
    
    def  form_valid(self, form):
        messages.success(self.request, "Votre mot de pass a ete bien modifier. Vous pouvez vous connectez")
        return super().form_valid(form)
    
            
