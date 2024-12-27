from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, contact, adresse, password=None):
        if not email:
            raise ValueError("L'adresse email doit etre fournie")

        user = self.model(
            email=self.normalize_email(email),
            first_name = first_name,
            last_name = last_name,
            contact = contact,
            adresse = adresse,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email,first_name, last_name, contact, adresse, password):
        user = self.create_user(
            email=email,
            password=password,
            first_name = first_name,
            last_name = last_name,
            contact = contact,
            adresse = adresse,
           
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    role_choices = (
        ("admin", "Admin"),
        ("associer", "Associer"),
    )
    email = models.EmailField(verbose_name="Adresse Email", unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    contact = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    adresse = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True, choices=role_choices, default="associer")
    
    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "Profile"

    def __str__(self) -> str:
        return self.email
