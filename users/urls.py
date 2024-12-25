from django.urls import include, path
from .views import *
urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login' ),
    path('register/', CustomUserCreationView.as_view(), name='register'),
    path('activation/<uid>/<token>/', ActivationUserView.as_view(), name='confirm_user_activation'),
    path('reset_password/', PasswordResetView.as_view(), name='reset_password'),
    path('password_confirm/<uid>/<token>/', CustomPasswordConfirmView.as_view(), name='password_confirmation'),
    path('', include('django.contrib.auth.urls')) 
]
