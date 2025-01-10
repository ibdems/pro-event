from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, contact, adresse, password=None):
        if not email:
            raise ValueError("L'adresse email doit etre fournie")

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            contact=contact,
            adresse=adresse,
        )
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
        ("member", "Membre"),
        ("organisateur", "Organisateur"),
    )
    email = models.EmailField(verbose_name="Adresse Email", unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nom")
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
    objects = UserManager()
    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "Utulisateur"

    def __str__(self) -> str:
        return self.email
