from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import get_complex_for_admin, is_complex_admin, is_superadmin

from .forms import ResidentForm, VisitorForm
from .models import Apartment, ResidentialComplex, Visitor


def _has_guard_access(user):
    return (
        user.is_authenticated and hasattr(user, 'staff_account') and
        getattr(user.staff_account, 'access_type', 'maintenance') == 'guard'
    )


def visitors_list(request):
    user = request.user
    is_guard = _has_guard_access(user)

    if not (is_superadmin(user) or is_complex_admin(user) or is_guard):
        return HttpResponseForbidden("Недостатньо прав.")

    complex_obj = None
    complexes = None
    selected_complex = request.GET.get('complex')

    if is_superadmin(user):
        complexes = ResidentialComplex.objects.order_by('name').all()
    elif is_guard:
        complex_obj = user.staff_account.staff.complex
    else:
        complex_obj = get_complex_for_admin(user)

    if request.method == 'POST':
        form = VisitorForm(request.POST, complex_obj=complex_obj) if complex_obj else VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.added_by = user
            visitor.save()
            if selected_complex:
                return redirect(f"{request.path}?complex={selected_complex}")
            return redirect('visitors_list')
    else:
        form = VisitorForm(complex_obj=complex_obj) if complex_obj else VisitorForm()
        if is_superadmin(user) and selected_complex:
            try:
                cid = int(selected_complex)
            except (ValueError, TypeError):
                cid = None
            if cid is not None:
                form.fields['apartment'].queryset = (
                    Apartment.objects
                    .filter(entrance__building__complex__complex_id=cid)
                    .select_related('entrance__building__complex')
                    .order_by('entrance__building__number', 'entrance__number', 'number')
                )

    visitors = Visitor.objects.select_related(
        'apartment',
        'apartment__entrance',
        'apartment__entrance__building',
        'added_by',
    )
    if complex_obj:
        visitors = visitors.filter(apartment__entrance__building__complex=complex_obj)
    elif selected_complex and is_superadmin(user):
        try:
            cid = int(selected_complex)
        except (ValueError, TypeError):
            cid = None
        if cid is not None:
            visitors = visitors.filter(apartment__entrance__building__complex__complex_id=cid)

    return render(request, 'complexes/visitors_list.html', {
        'visitors': visitors.order_by('-created_at'),
        'form': form,
        'complex': complex_obj,
        'complexes': complexes,
        'selected_complex': int(selected_complex) if selected_complex else None,
    })


@login_required
def resident_quick_add(request):
    if not _has_guard_access(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    complex_obj = staff.complex

    if request.method == 'POST':
        form = ResidentForm(request.POST, complex_obj=complex_obj)
        if form.is_valid():
            form.save()
            return redirect('resident_quick_add')
    else:
        form = ResidentForm(complex_obj=complex_obj)

    return render(request, 'complexes/simple_form.html', {
        'title': 'Додати мешканця',
        'form': form,
    })


@login_required
def visitor_delete(request, pk):
    if is_superadmin(request.user):
        complex_filter = {}
    elif _has_guard_access(request.user):
        complex_filter = {
            'apartment__entrance__building__complex_id': request.user.staff_account.staff.complex_id,
        }
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if complex_obj is None:
            return HttpResponseForbidden("Доступ заборонено.")
        complex_filter = {
            'apartment__entrance__building__complex_id': complex_obj.pk,
        }
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    visitor = get_object_or_404(
        Visitor.objects.select_related(
            'apartment', 'apartment__entrance', 'apartment__entrance__building'
        ),
        pk=pk,
        **complex_filter,
    )

    if request.method == 'POST':
        visitor.delete()
        return redirect('visitors_list')

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити відвідувача: {visitor.fullname}?",
    })
