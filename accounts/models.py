from django.conf import settings
from django.db import models
from complexes.models import ResidentialComplex, Owner, Staff

User = settings.AUTH_USER_MODEL


class ComplexAdminProfile(models.Model):
    """
    Адміністратор житлового комплексу.
    Прив'язаний до одного ЖК.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='complex_admin_profile')
    complex = models.ForeignKey(ResidentialComplex, on_delete=models.CASCADE, related_name='admins')

    def __str__(self):
        return f"ComplexAdmin {self.user} -> {self.complex.name}"


class OwnerAccount(models.Model):
    """
    Акаунт власника, прив'язаний до запису Owner.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_account')
    owner = models.OneToOneField(Owner, on_delete=models.CASCADE, related_name='account')

    def __str__(self):
        return f"OwnerAccount {self.user} -> {self.owner.name}"


class StaffAccount(models.Model):
    """
    Акаунт співробітника ЖК (охорона, техперсонал).
    Частина staff може існувати без акаунта.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_account')
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name='account')
    ACCESS_CHOICES = [
        ('guard', 'Охорона'),
        ('maintenance', 'Техпрацівник'),
    ]
    access_type = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='maintenance')

    def __str__(self):
        return f"StaffAccount {self.user} -> {self.staff.fullname} ({self.staff.role}), access={self.access_type}"
