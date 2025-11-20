from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ComplexAdminUpdateForm,
    OwnerAccountUpdateForm,
    StaffAccountUpdateForm,
)
from .models import ComplexAdminProfile, OwnerAccount, StaffAccount
from .utils import get_complex_for_admin, is_superadmin, superadmin_required


# ===== Edit/Delete: Complex Admin (superadmin only) =====

@superadmin_required
def edit_complex_admin(request, pk):
    profile = get_object_or_404(ComplexAdminProfile, pk=pk)
    if request.method == 'POST':
        form = ComplexAdminUpdateForm(request.POST, instance=profile.user, profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Обліковий запис адміністратора ЖК оновлено.")
            return redirect('accounts:dashboard')
    else:
        form = ComplexAdminUpdateForm(instance=profile.user, profile=profile)

    return render(request, 'accounts/create_user.html', {
        'title': 'Редагувати адміністратора ЖК',
        'form': form,
    })


@superadmin_required
def delete_complex_admin(request, pk):
    profile = get_object_or_404(ComplexAdminProfile, pk=pk)
    if request.method == 'POST':
        username = profile.user.username
        profile.user.delete()
        messages.success(request, f"Користувача '{username}' видалено разом з профілем адміністратора ЖК.")
        return redirect('accounts:dashboard')
    return render(request, 'complexes/confirm_delete.html', {
        'title': 'Видалити адміністратора ЖК?'
    })


# ===== Edit/Delete: Owner account (superadmin or complex admin of related complex) =====

def _user_can_manage_owner_account(user, owner_account: OwnerAccount) -> bool:
    if is_superadmin(user):
        return True
    complex_obj = get_complex_for_admin(user)
    if complex_obj is None:
        return False
    return owner_account.owner.apartments.filter(entrance__building__complex=complex_obj).exists()


@login_required
def edit_owner_account(request, pk):
    account = get_object_or_404(OwnerAccount.objects.select_related('user', 'owner'), pk=pk)
    if not _user_can_manage_owner_account(request.user, account):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = OwnerAccountUpdateForm(request.POST, instance=account.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Обліковий запис власника оновлено.")
            return redirect('accounts:dashboard')
    else:
        form = OwnerAccountUpdateForm(instance=account.user)

    return render(request, 'accounts/create_user.html', {
        'title': 'Редагувати акаунт власника',
        'form': form,
    })


@login_required
def delete_owner_account(request, pk):
    account = get_object_or_404(OwnerAccount.objects.select_related('user', 'owner'), pk=pk)
    if not _user_can_manage_owner_account(request.user, account):
        return HttpResponseForbidden()

    if request.method == 'POST':
        username = account.user.username
        account.user.delete()
        messages.success(request, f"Користувача-власника '{username}' видалено.")
        return redirect('accounts:dashboard')
    return render(request, 'complexes/confirm_delete.html', {
        'title': 'Видалити акаунт власника?'
    })


# ===== Edit/Delete: Staff account (superadmin or complex admin of same complex) =====

def _user_can_manage_staff_account(user, staff_account: StaffAccount) -> bool:
    if is_superadmin(user):
        return True
    complex_obj = get_complex_for_admin(user)
    if complex_obj is None:
        return False
    return staff_account.staff.complex_id == complex_obj.pk


@login_required
def edit_staff_account(request, pk):
    account = get_object_or_404(StaffAccount.objects.select_related('user', 'staff'), pk=pk)
    if not _user_can_manage_staff_account(request.user, account):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = StaffAccountUpdateForm(request.POST, instance=account.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Обліковий запис співробітника оновлено.")
            return redirect('accounts:dashboard')
    else:
        form = StaffAccountUpdateForm(instance=account.user)

    return render(request, 'accounts/create_user.html', {
        'title': 'Редагувати акаунт співробітника',
        'form': form,
    })


@login_required
def delete_staff_account(request, pk):
    account = get_object_or_404(StaffAccount.objects.select_related('user', 'staff'), pk=pk)
    if not _user_can_manage_staff_account(request.user, account):
        return HttpResponseForbidden()

    if request.method == 'POST':
        username = account.user.username
        account.user.delete()
        messages.success(request, f"Користувача-співробітника '{username}' видалено.")
        return redirect('accounts:dashboard')
    return render(request, 'complexes/confirm_delete.html', {
        'title': 'Видалити акаунт співробітника?'
    })

