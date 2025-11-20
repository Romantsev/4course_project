from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import ComplexAdminProfile, OwnerAccount, StaffAccount
from complexes.models import ResidentialComplex
from .forms import (
    ComplexAdminCreateForm,
    OwnerAccountCreateForm,
    StaffAccountCreateForm,
    ComplexAdminUpdateForm,
    OwnerAccountUpdateForm,
    StaffAccountUpdateForm,
)
from .utils import (
    is_superadmin,
    get_complex_for_admin,
    superadmin_required,
    complex_admin_required,
)


@login_required
def dashboard(request):
    user = request.user

    if is_superadmin(user):
        complex_admins = ComplexAdminProfile.objects.select_related('user', 'complex')
        return render(request, 'accounts/dashboard_superadmin.html', {
            'complex_admins': complex_admins,
        })

    if hasattr(user, 'complex_admin_profile'):
        complex_id = user.complex_admin_profile.complex_id
        owner_accounts = OwnerAccount.objects.filter(
            owner__apartments__entrance__building__complex_id=complex_id
        ).select_related('user', 'owner').distinct()
        staff_accounts = StaffAccount.objects.filter(
            staff__complex_id=complex_id
        ).select_related('user', 'staff')
        return render(request, 'accounts/dashboard_complex_admin.html', {
            'complex': user.complex_admin_profile.complex,
            'owner_accounts': owner_accounts,
            'staff_accounts': staff_accounts,
        })

    if hasattr(user, 'owner_account'):
        owner = user.owner_account.owner
        apartments = owner.apartments.select_related(
            'entrance', 'entrance__building', 'entrance__building__complex'
        )
        return render(request, 'accounts/dashboard_owner.html', {
            'owner': owner,
            'apartments': apartments,
        })

    if hasattr(user, 'staff_account'):
        staff = user.staff_account.staff
        return render(request, 'accounts/dashboard_staff.html', {
            'staff': staff,
        })

    return render(request, 'accounts/dashboard_generic.html')


@superadmin_required
def create_complex_admin(request):
    if request.method == 'POST':
        form = ComplexAdminCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            complex_obj = form.cleaned_data['complex']
            ComplexAdminProfile.objects.create(user=user, complex=complex_obj)
            messages.success(request, "Створено адміністратора ЖК.")
            return redirect('accounts:dashboard')
    else:
        form = ComplexAdminCreateForm()

    return render(request, 'accounts/create_user.html', {
        'title': 'Створити адміністратора ЖК',
        'form': form,
    })


@complex_admin_required
def create_owner_account(request):
    complex_obj = get_complex_for_admin(request.user)

    if request.method == 'POST':
        form = OwnerAccountCreateForm(request.POST, complex_obj=complex_obj)
        if form.is_valid():
            user = form.save()
            owner = form.cleaned_data['owner']
            OwnerAccount.objects.create(user=user, owner=owner)
            messages.success(request, "Створено акаунт власника.")
            return redirect('accounts:dashboard')
    else:
        form = OwnerAccountCreateForm(complex_obj=complex_obj)

    return render(request, 'accounts/create_user.html', {
        'title': 'Створити акаунт власника',
        'form': form,
    })


@complex_admin_required
def create_staff_account(request):
    complex_obj = get_complex_for_admin(request.user)

    if request.method == 'POST':
        form = StaffAccountCreateForm(request.POST, complex_obj=complex_obj)
        if form.is_valid():
            user = form.save()
            staff = form.cleaned_data['staff']
            StaffAccount.objects.create(user=user, staff=staff, access_type=(form.cleaned_data.get('access_type') or 'maintenance'))
            messages.success(request, "Створено акаунт співробітника.")
            return redirect('accounts:dashboard')
    else:
        form = StaffAccountCreateForm(complex_obj=complex_obj)

    return render(request, 'accounts/create_user.html', {
        'title': 'Створити акаунт співробітника',
        'form': form,
    })
