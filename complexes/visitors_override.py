from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from accounts.utils import is_superadmin, is_complex_admin, get_complex_for_admin
from .models import Visitor, Apartment, ResidentialComplex
from .forms import VisitorForm as _VisitorForm


@login_required
def visitors_list(request):
    user = request.user

    is_guard = (
        user.is_authenticated
        and hasattr(user, 'staff_account')
        and getattr(user.staff_account, 'access_type', 'maintenance') == 'guard'
    )

    # Доступ: SuperAdmin, ComplexAdmin, охоронець
    if not (is_superadmin(user) or is_complex_admin(user) or is_guard):
        return HttpResponseForbidden("Недостатньо прав.")

    complex_obj = None
    complexes = None
    selected_complex = request.GET.get('complex')

    if is_superadmin(user):
        complexes = ResidentialComplex.objects.order_by('name').all()
    elif is_guard and hasattr(user, 'staff_account'):
        staff = user.staff_account.staff
        complex_obj = staff.complex
    elif is_complex_admin(user):
        complex_obj = get_complex_for_admin(user)

    if request.method == 'POST':
        form = _VisitorForm(request.POST, complex_obj=complex_obj) if complex_obj else _VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.added_by = request.user
            visitor.save()
            if selected_complex:
                return redirect(f"{request.path}?complex={selected_complex}")
            return redirect('visitors_list')
    else:
        form = _VisitorForm(complex_obj=complex_obj) if complex_obj else _VisitorForm()
        if is_superadmin(request.user) and selected_complex:
            try:
                cid = int(selected_complex)
                apartments_qs = Apartment.objects.filter(
                    entrance__building__complex__complex_id=cid
                ).select_related('entrance__building__complex').order_by(
                    'entrance__building__number', 'entrance__number', 'number'
                )
                form.fields['apartment'].queryset = apartments_qs
            except (ValueError, TypeError):
                pass

    visitors = (
        Visitor.objects
        .select_related('apartment', 'apartment__entrance', 'apartment__entrance__building', 'added_by')
    )
    if complex_obj:
        visitors = visitors.filter(apartment__entrance__building__complex=complex_obj)
    elif selected_complex and is_superadmin(request.user):
        try:
            cid = int(selected_complex)
            visitors = visitors.filter(apartment__entrance__building__complex__complex_id=cid)
        except (ValueError, TypeError):
            pass

    visitors = visitors.order_by('-created_at')

    return render(request, 'complexes/visitors_list.html', {
        'visitors': visitors,
        'form': form,
        'complex': complex_obj,
        'complexes': complexes,
        'selected_complex': int(selected_complex) if selected_complex else None,
    })
