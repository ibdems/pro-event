from allauth.socialaccount.models import SocialAccount
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=SocialAccount)
def update_user_image(sender, instance, **kwargs):
    user = instance.user  # Utilisateur lié au compte social
    if not user.image:  # Si aucune image n'est déjà définie
        if instance.provider == "google":
            user.image = instance.extra_data.get("picture")  # Correctement lié au champ image
        elif instance.provider == "facebook":
            user.image = instance.extra_data.get("picture", {}).get("data", {}).get("url")
        elif instance.provider == "github":
            user.image = instance.extra_data.get("avatar_url")
        user.save()
