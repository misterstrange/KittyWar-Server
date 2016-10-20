from django.db import models


class CatCard(models.Model):
    breed = models.CharField(max_length=30)
    health = models.PositiveIntegerField(default=10)
    AbAttribute = models.CharField(max_length=30)
    AbText = models.CharField(max_length=100)
    flavor = models.CharField(max_length=100)


class BasicCards(models.Model):
    Title = models.CharField(max_length=10)
    attribute = models.CharField(max_length=10)
    AbAttribute = models.CharField(max_length=10)
    AbText = models.CharField(max_length=100)
    flavor = models.CharField(max_length=100)
