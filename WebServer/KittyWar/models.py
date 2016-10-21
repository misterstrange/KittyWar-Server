from django.db import models


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
