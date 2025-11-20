from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import ComplexAdminProfile, OwnerAccount, StaffAccount


User = get_user_model()


def _user_has_any_account(user: User) -> bool:
    """Return True if user still has any linked account/profile.

    Use queries instead of attribute access to avoid RelatedObjectDoesNotExist.
    """
    if not user or not isinstance(user, User):
        return False
    return (
        OwnerAccount.objects.filter(user=user).exists()
        or StaffAccount.objects.filter(user=user).exists()
        or ComplexAdminProfile.objects.filter(user=user).exists()
    )


def _try_delete_user(user: User):
    """Delete user if not superuser and has no other linked accounts."""
    if not user:
        return
    if getattr(user, "is_superuser", False):
        return
    if _user_has_any_account(user):
        return
    # No other roles left — remove the auth user record.
    user.delete()


@receiver(post_delete, sender=OwnerAccount)
def _owner_account_deleted(sender, instance: OwnerAccount, **kwargs):
    _try_delete_user(getattr(instance, "user", None))


@receiver(post_delete, sender=StaffAccount)
def _staff_account_deleted(sender, instance: StaffAccount, **kwargs):
    _try_delete_user(getattr(instance, "user", None))


@receiver(post_delete, sender=ComplexAdminProfile)
def _complex_admin_deleted(sender, instance: ComplexAdminProfile, **kwargs):
    _try_delete_user(getattr(instance, "user", None))

