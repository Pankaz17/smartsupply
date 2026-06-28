from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from common.models import TimeStampedModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'owner')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        STAFF = 'staff', 'Staff'

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STAFF,
    )
    full_name = models.CharField(max_length=150, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['email']

    def __str__(self):
        return self.email

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if not self.full_name:
            self.full_name = self.get_full_name() or self.email
        super().save(*args, **kwargs)


class BusinessSettings(TimeStampedModel):
    """Single-store configuration. Only one row should exist."""

    store_name = models.CharField(max_length=200, default='My Store')
    currency = models.CharField(max_length=3, default='USD')
    dead_stock_threshold_days = models.PositiveIntegerField(
        default=90,
        help_text='Days without a sale before a product is flagged as dead stock.',
    )
    seasonal_alert_window_days = models.PositiveIntegerField(
        default=14,
        help_text='Days ahead to alert owners about upcoming seasonal events.',
    )

    class Meta:
        verbose_name_plural = 'Business settings'

    def __str__(self):
        return self.store_name

    @classmethod
    def get_solo(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
