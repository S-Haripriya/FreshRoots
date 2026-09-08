from django.db import models
from django.contrib.auth.models import User

class Contact(models.Model):
    c_number = models.IntegerField(max_length=10)
    c_email = models.CharField()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE )

    contact_number = models.CharField(max_length=15)
    @property
    def is_verified_producer(self):
        return self.farms.filter(is_verified=True).exists()
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
        