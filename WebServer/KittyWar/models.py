from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=24)

    def logged_in(self):

        if self.token != '':
            return True
        return False


class CatCard(models.Model):
    
    breed = models.CharField(max_length=30)
    health = models.PositiveIntegerField(default=10)
    attribute_id = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    flavor = models.CharField(max_length=100)


class BasicCards(models.Model):
    
    title = models.CharField(max_length=10)
    attribute_id = models.CharField(max_length=10)
    description = models.CharField(max_length=100)
    flavor = models.CharField(max_length=100)
