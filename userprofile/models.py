from django.db import models
from core.models import UserProfile

class GetCertified(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete = models.CASCADE, related_name ='farms')

    is_verified = models.BooleanField(default= False)
    farm_name = models.TextField()
    farm_address = models.TextField()
    farm_type = models.TextField()
    certificate = models.FileField(upload_to='certificates/',blank=True,null=True)

    def __str__(self):
        return self.farm_name

