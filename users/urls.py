from django.urls import path

from .views import (
    ActivationUserView,
    CustomLoginView,
    CustomPasswordResetCompleteView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
    CustomUserCreationView,
    lock,
    logout_view,
)

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("register/", CustomUserCreationView.as_view(), name="signup"),
    path("activation/<uid>/<token>/", ActivationUserView.as_view(), name="confirm_user_activation"),
    path(
        "accounts/activation/<uid>/<token>/",
        ActivationUserView.as_view(),
        name="accounts_user_activation",
    ),
    # URLs de réinitialisation de mot de passe
    path("reset_password/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("reset_password/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="accounts_password_reset_confirm",
    ),
    path(
        "reset/done/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # Autres URLs
    path("lock/", lock, name="lock"),
    path("logout/", logout_view, name="logout"),
]
