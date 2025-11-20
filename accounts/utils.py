from django.contrib.auth.decorators import user_passes_test
from .models import ComplexAdminProfile
from complexes.models import ResidentialComplex


def is_superadmin(user):
    """
    Системний адміністратор платформи.
    Використовуємо is_superuser (основний критерій).
    """
    return user.is_authenticated and user.is_superuser


def is_complex_admin(user):
    """
    Користувач, прив'язаний як ComplexAdminProfile.
    """
    return user.is_authenticated and ComplexAdminProfile.objects.filter(user=user).exists()


def get_complex_for_admin(user):
    """
    ЖК, за який відповідає Complex Admin.
    """
    try:
        return user.complex_admin_profile.complex
    except ComplexAdminProfile.DoesNotExist:
        return None


def user_can_manage_complex(user, complex_obj: ResidentialComplex) -> bool:
    """
    Чи може користувач керувати цим ЖК:
    - SuperAdmin — завжди
    - ComplexAdmin — тільки своїм
    """
    if not user.is_authenticated:
        return False
    if is_superadmin(user):
        return True
    return ComplexAdminProfile.objects.filter(user=user, complex=complex_obj).exists()


superadmin_required = user_passes_test(is_superadmin)
complex_admin_required = user_passes_test(is_complex_admin)
