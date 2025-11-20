from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Owner, Resident, Staff, ResidentialComplex, Apartment
from accounts.utils import is_superadmin, is_complex_admin, get_complex_for_admin
from .models import Owner, Resident, Staff
from .forms import OwnerForm, ResidentForm, StaffForm


def owners_list(request):
    if is_superadmin(request.user):
        if request.method == 'POST':
            form = OwnerForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('owners_list')
        else:
            form = OwnerForm()
        owners = Owner.objects.all().order_by('name')
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        owners = (
            Owner.objects
            .filter(apartments__entrance__building__complex=complex_obj)
            .order_by('name')
            .distinct()
        )
        form = None
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    return render(request, 'complexes/owners_list.html', {
        'owners': owners,
        'form': form,
    })


def residents_list(request):
    complexes = ResidentialComplex.objects.order_by('name').all()

    selected_complex = request.GET.get('complex')

    if is_superadmin(request.user):
        if request.method == 'POST':
            form = ResidentForm(request.POST)
            if form.is_valid():
                form.save()
                if selected_complex:
                    return redirect(f"{request.path}?complex={selected_complex}")
                return redirect('residents_list')
        else:
            form = ResidentForm()
        residents_qs = Resident.objects.select_related(
            'apartment__entrance__building__complex'
        ).order_by('fullname')

        if selected_complex:
            try:
                cid = int(selected_complex)
                residents_qs = residents_qs.filter(
                    apartment__entrance__building__complex__complex_id=cid
                )
            except (ValueError, TypeError):
                pass

        if form is not None and selected_complex:
            try:
                cid = int(selected_complex)
                apartments_qs = Apartment.objects.filter(
                    entrance__building__complex__complex_id=cid
                ).select_related('entrance__building__complex').order_by(
                    'entrance__building__number', 'entrance__number', 'number'
                )
                form.fields['apartment'].queryset = apartments_qs
            except Exception:
                pass

    elif is_complex_admin(request.user):
        # complex admin бачить лише мешканців свого комплексу — без можливості змінювати фільтр
        complex_obj = get_complex_for_admin(request.user)
        form = None
        residents_qs = (
            Resident.objects
            .select_related('apartment__entrance__building__complex')
            .filter(apartment__entrance__building__complex=complex_obj)
            .order_by('fullname')
        )
        selected_complex = complex_obj.complex_id
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    return render(request, 'complexes/residents_list.html', {
        'residents': residents_qs,
        'form': form,
        'complexes': complexes,
        'selected_complex': int(selected_complex) if selected_complex else None,
    })



def staff_list(request):
    if is_superadmin(request.user):
        if request.method == 'POST':
            form = StaffForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('staff_list')
        else:
            form = StaffForm()
        staff = Staff.objects.select_related('complex').order_by('fullname')
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if request.method == 'POST':
            form = StaffForm(request.POST, complex_obj=complex_obj)
            if form.is_valid():
                staff_obj = form.save(commit=False)
                staff_obj.complex = complex_obj  # enforce ownership
                staff_obj.save()
                return redirect('staff_list')
        else:
            form = StaffForm(complex_obj=complex_obj)
        staff = Staff.objects.filter(complex=complex_obj).order_by('fullname')
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    return render(request, 'complexes/staff_list.html', {
        'staff_list': staff,
        'form': form,
    })


def resident_edit(request, pk):
    if not is_superadmin(request.user):
        return HttpResponseForbidden("Доступ заборонено.")
    resident = get_object_or_404(Resident, pk=pk)
    if request.method == 'POST':
        form = ResidentForm(request.POST, instance=resident)
        if form.is_valid():
            form.save()
            return redirect('residents_list')
    else:
        form = ResidentForm(instance=resident)
    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати мешканця: {resident.fullname}",
        'form': form,
    })


def resident_delete(request, pk):
    if not is_superadmin(request.user):
        return HttpResponseForbidden("Доступ заборонено.")
    resident = get_object_or_404(Resident, pk=pk)
    if request.method == 'POST':
        resident.delete()
        return redirect('residents_list')
    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити мешканця: {resident.fullname}?",
    })


def staff_edit(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if is_superadmin(request.user):
        pass
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if staff.complex_id != complex_obj.pk:
            return HttpResponseForbidden("Доступ заборонено.")
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    if request.method == 'POST':
        kwargs = {}
        if is_complex_admin(request.user):
            kwargs['complex_obj'] = get_complex_for_admin(request.user)
        form = StaffForm(request.POST, instance=staff, **kwargs)
        if form.is_valid():
            staff_obj = form.save(commit=False)
            if is_complex_admin(request.user):
                staff_obj.complex = get_complex_for_admin(request.user)
            staff_obj.save()
            return redirect('staff_list')
    else:
        kwargs = {}
        if is_complex_admin(request.user):
            kwargs['complex_obj'] = get_complex_for_admin(request.user)
        form = StaffForm(instance=staff, **kwargs)
    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати співробітника: {staff.fullname}",
        'form': form,
    })


def staff_delete(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if is_superadmin(request.user):
        pass
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if staff.complex_id != complex_obj.pk:
            return HttpResponseForbidden("Доступ заборонено.")
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    if request.method == 'POST':
        staff.delete()
        return redirect('staff_list')
    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити співробітника: {staff.fullname}?",
    })
