from django.db import models


class Post(models.Model):
    login = models.CharField(max_length=300)
    password = models.CharField(max_length=300)
