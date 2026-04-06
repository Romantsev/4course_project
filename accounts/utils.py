from functools import wraps

from django.contrib.auth.views import redirect_to_login

from residence_manager.responses import forbidden_response
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


def _role_required(test_func):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not test_func(request.user):
                return forbidden_response(request)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


superadmin_required = _role_required(is_superadmin)
complex_admin_required = _role_required(is_complex_admin)
