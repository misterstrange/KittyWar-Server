from django.db import models
from django.contrib.auth.models import User


class AbilityCards(models.Model):
    CARD_PHASES = (
        (0, 'Any'),
        (1, 'Prelude'),
        (2, 'Enacting strategies'),
        (3, 'Showing Cards'),
        (4, 'Strategy settlement'),
        (5, 'Postlude'),
    )
    title = models.CharField(max_length=10)
    id = models.CharField(max_length=30)
    phase = models.PositiveIntegerField(1, choices=CARD_PHASES, default=0)
    cooldown = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=100)


class CatCard(models.Model):
    
    title = models.CharField(max_length=30)
    health = models.PositiveIntegerField(default=10)
    default = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=100)
    flavor = models.CharField(max_length=100)
    ability_id = models.CharField(max_length=10)


class BasicCards(models.Model):
    
    title = models.CharField(max_length=10)
    id = models.CharField(max_length=10)
    description = models.CharField(max_length=100)
    flavor = models.CharField(max_length=100)


class UserProfile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=24)
    wins = models.PositiveIntegerField(default=0)
    loss = models.PositiveIntegerField(default=0)
    draw = models.PositiveIntegerField(default=0)
    cats = models.ManyToManyField(CatCard)

    def logged_in(self):

        if self.token != '':
            return True
        return False
