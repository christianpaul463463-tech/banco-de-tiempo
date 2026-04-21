from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    bio = models.TextField(blank=True)
    skills = models.TextField(blank=True)  # habilidades que ofrece
    time_balance = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)  # horas iniciales
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
