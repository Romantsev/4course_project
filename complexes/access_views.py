from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from .models import Visitor
from .forms import VisitorForm


def _staff_role(user):
    if not (user.is_authenticated and hasattr(user, 'staff_account')):
        return None
    return (user.staff_account.staff.role or '').strip().lower()


def _is_guard(user):
    role = _staff_role(user)
    if not role:
        return False
    guard_synonyms = ['охоронець', 'охорона', 'guard', 'security']
    return any(s in role for s in guard_synonyms)


@login_required
def visitors_list(request):
    if not _is_guard(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    complex_obj = staff.complex

    if request.method == 'POST':
        form = VisitorForm(request.POST, complex_obj=complex_obj)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.added_by = request.user
            visitor.save()
            return redirect('visitors_list')
    else:
        form = VisitorForm(complex_obj=complex_obj)

    visitors = (
        Visitor.objects
        .select_related(
            'apartment',
            'apartment__entrance',
            'apartment__entrance__building',
            'added_by',
        )
        .filter(apartment__entrance__building__complex=complex_obj)
        .order_by('-created_at')
    )

    return render(request, 'complexes/visitors_list.html', {
        'visitors': visitors,
        'form': form,
        'complex': complex_obj,
    })


from .forms import VisitorForm as _VisitorForm, ResidentForm
from accounts.utils import is_superadmin


def _has_guard_access(user):
    return (
        user.is_authenticated and hasattr(user, 'staff_account') and
        getattr(user.staff_account, 'access_type', 'maintenance') == 'guard'
    )


@login_required
def visitors_list(request):
    if not _has_guard_access(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    complex_obj = staff.complex

    if request.method == 'POST':
        form = _VisitorForm(request.POST, complex_obj=complex_obj)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.added_by = request.user
            visitor.save()
            return redirect('visitors_list')
    else:
        form = _VisitorForm(complex_obj=complex_obj)

    visitors = (
        Visitor.objects
        .select_related(
            'apartment',
            'apartment__entrance',
            'apartment__entrance__building',
            'added_by',
        )
        .filter(apartment__entrance__building__complex=complex_obj)
        .order_by('-created_at')
    )

    return render(request, 'complexes/visitors_list.html', {
        'visitors': visitors,
        'form': form,
        'complex': complex_obj,
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
    # SuperAdmin: full access regardless of guard role/complex
    if is_superadmin(request.user):
        visitor = get_object_or_404(
            Visitor.objects.select_related(
                'apartment', 'apartment__entrance', 'apartment__entrance__building'
            ),
            pk=pk,
        )
        if request.method == 'POST':
            visitor.delete()
            return redirect('visitors_list')
        return render(request, 'complexes/confirm_delete.html', {
            'title': f"Видалити відвідувача: {visitor.fullname}?",
        })
    if not _has_guard_access(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    visitor = get_object_or_404(
        Visitor.objects.select_related(
            'apartment', 'apartment__entrance', 'apartment__entrance__building'
        ),
        pk=pk,
        apartment__entrance__building__complex_id=staff.complex_id,
    )

    if request.method == 'POST':
        visitor.delete()
        return redirect('visitors_list')

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити відвідувача: {visitor.fullname}?",
    })
