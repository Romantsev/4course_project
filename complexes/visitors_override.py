from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from accounts.utils import is_superadmin
from .models import Visitor, Apartment, ResidentialComplex
from .forms import VisitorForm as _VisitorForm


@login_required
def visitors_list(request):
    if not (is_superadmin(request.user) or (
        request.user.is_authenticated and hasattr(request.user, 'staff_account') and
        getattr(request.user.staff_account, 'access_type', 'maintenance') == 'guard'
    )):
        return HttpResponseForbidden("Недостатньо прав.")
    complex_obj = None
    if not is_superadmin(request.user) and hasattr(request.user, 'staff_account'):
        staff = request.user.staff_account.staff
        complex_obj = staff.complex
    complexes = None
    selected_complex = request.GET.get('complex')
    if is_superadmin(request.user):
        complexes = ResidentialComplex.objects.order_by('name').all()

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
