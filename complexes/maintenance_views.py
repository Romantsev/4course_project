from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.db.models import Prefetch

from .models import MaintenanceRequest
from .maintenance_forms import MaintenanceRequestForm


def _is_owner(user):
    return user.is_authenticated and hasattr(user, 'owner_account')


def _has_technician_access(user):
    return (
        user.is_authenticated and hasattr(user, 'staff_account') and
        getattr(user.staff_account, 'access_type', 'maintenance') == 'maintenance'
    )


@login_required
def tickets_owner_list(request):
    if not _is_owner(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    owner = request.user.owner_account.owner
    tickets = (
        MaintenanceRequest.objects
        .select_related('apartment', 'apartment__entrance', 'apartment__entrance__building')
        .filter(owner=owner)
        .order_by('-created_at')
    )

    return render(request, 'complexes/tickets_owner_list.html', {
        'owner': owner,
        'tickets': tickets,
    })


@login_required
def ticket_create(request):
    if not _is_owner(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    owner = request.user.owner_account.owner

    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, owner=owner)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.owner = owner
            ticket.status = 'new'
            ticket.save()
            return redirect('tickets_owner_list')
    else:
        form = MaintenanceRequestForm(owner=owner)

    return render(request, 'complexes/simple_form.html', {
        'title': "Створити заявку на ремонт",
        'form': form,
    })


@login_required
def tickets_staff_list(request):
    if not _has_technician_access(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    complex_id = staff.complex_id

    base_qs = (
        MaintenanceRequest.objects
        .select_related(
            'owner',
            'apartment',
            'apartment__entrance',
            'apartment__entrance__building',
            'apartment__entrance__building__complex',
        )
        .filter(apartment__entrance__building__complex_id=complex_id)
        .order_by('status', '-created_at')
    )

    tickets_new = base_qs.filter(status='new')
    tickets_in_progress = base_qs.filter(status='in_progress')
    tickets_done = base_qs.filter(status='done')

    return render(request, 'complexes/tickets_staff_list.html', {
        'staff': staff,
        'tickets_new': tickets_new,
        'tickets_in_progress': tickets_in_progress,
        'tickets_done': tickets_done,
    })


@login_required
def ticket_take(request, pk):
    if not _has_technician_access(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    ticket = get_object_or_404(
        MaintenanceRequest,
        pk=pk,
        apartment__entrance__building__complex_id=staff.complex_id,
    )

    if request.method == 'POST':
        ticket.status = 'in_progress'
        ticket.save(update_fields=['status', 'updated_at'])
        return redirect('tickets_staff_list')

    return render(request, 'complexes/confirm_delete.html', {
        'title': 'Почати виконання заявки?',
    })


@login_required
def ticket_done(request, pk):
    if not _has_technician_access(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    ticket = get_object_or_404(
        MaintenanceRequest,
        pk=pk,
        apartment__entrance__building__complex_id=staff.complex_id,
    )

    if request.method == 'POST':
        ticket.status = 'done'
        ticket.save(update_fields=['status', 'updated_at'])
        return redirect('tickets_staff_list')

    return render(request, 'complexes/confirm_delete.html', {
        'title': 'Позначити заявку як виконану?',
    })


@login_required
def ticket_delete(request, pk):
    if not _has_technician_access(request.user):
        return HttpResponseForbidden("Доступ заборонено.")

    staff = request.user.staff_account.staff
    ticket = get_object_or_404(
        MaintenanceRequest,
        pk=pk,
        apartment__entrance__building__complex_id=staff.complex_id,
    )

    if ticket.status != 'done':
        return HttpResponseForbidden("Видаляти можна лише виконані заявки.")

    if request.method == 'POST':
        ticket.delete()
        return redirect('tickets_staff_list')

    return render(request, 'complexes/confirm_delete.html', {
        'title': 'Видалити виконану заявку?'
    })
