# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django_extensions.db.fields import AutoSlugField
from .managers import UserManager, EntesManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=80, blank=False)
    slug = AutoSlugField(populate_from='name', overwrite=True)

    is_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    entes = EntesManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    @property
    def is_staff(self):
        return self.is_admin

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name.split(' ')[0]


class Ente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cpf = models.CharField(max_length=15, blank=True)
    cnpj = models.CharField(max_length=20, blank=True)
    ceac = models.PositiveSmallIntegerField(
        blank=False,
        validators=[MaxValueValidator(9999)]
    )

    objects = EntesManager()

    def __str__(self):
        return "{cpf}: {name}".format(cpf=self.cpf, name=self.user.name)
