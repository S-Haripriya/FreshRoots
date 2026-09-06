from django.db import models
from django.contrib.auth.models import User

class Contact(models.Model):
    c_number = models.IntegerField(max_length=10)
    c_email = models.CharField()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE )

    is_verified = models.BooleanField(default=False)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
        