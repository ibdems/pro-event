from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, first_name=None, last_name=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.model(
            email=email,
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    role_choices = (
        ("membre", "Membre"),
        ("organisateur", "Organisateur"),
    )
    email = models.EmailField(verbose_name="Adresse Email", unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nom")
    contact = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    adresse = models.CharField(max_length=100, null=True, blank=True)
    photo = models.ImageField("photo_user/", blank=True, null=True)
    role = models.CharField(
        max_length=255, null=True, blank=True, choices=role_choices, default="membre"
    )
    created_at = models.DateTimeField(
        default=timezone.now, null=True, verbose_name="Date de creation"
    )
    update_at = models.DateTimeField(auto_now=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    activation_token = models.CharField(max_length=64, blank=True, null=True)
    activation_token_created_at = models.DateTimeField(null=True, blank=True)
    objects = UserManager()
    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "Utulisateur"

    def __str__(self) -> str:
        return self.email

    def get_full_name(self):
        """
        Retourne le nom complet de l'utilisateur, ou l'email si le nom n'est pas défini
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def get_short_name(self):
        """
        Retourne le prénom de l'utilisateur, ou l'email si le prénom n'est pas défini
        """
        return self.first_name or self.email
