from django.contrib.auth.decorators import login_required
from django.core import signing
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.utils import get_complex_for_admin, is_complex_admin, is_superadmin
from residence_manager.responses import forbidden_response

from .forms import ResidentForm, VisitorForm
from .models import Apartment, ResidentialComplex, Visitor


def _has_guard_access(user):
    return (
        user.is_authenticated
        and hasattr(user, 'staff_account')
        and getattr(user.staff_account, 'access_type', 'maintenance') == 'guard'
    )


def _get_visitor_queryset_for_user(user):
    queryset = Visitor.objects.select_related(
        'apartment',
        'apartment__entrance',
        'apartment__entrance__building',
        'apartment__entrance__building__complex',
        'added_by',
    )

    if is_superadmin(user):
        return queryset

    if _has_guard_access(user):
        return queryset.filter(
            apartment__entrance__building__complex_id=user.staff_account.staff.complex_id,
        )

    if is_complex_admin(user):
        complex_obj = get_complex_for_admin(user)
        if complex_obj is None:
            return None
        return queryset.filter(apartment__entrance__building__complex_id=complex_obj.pk)

    return None


def visitors_list(request):
    user = request.user
    is_guard = _has_guard_access(user)

    if not (is_superadmin(user) or is_complex_admin(user) or is_guard):
        return forbidden_response(request)

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
        form = (
            VisitorForm(request.POST, complex_obj=complex_obj)
            if complex_obj
            else VisitorForm(request.POST)
        )
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
                    Apartment.objects.filter(entrance__building__complex__complex_id=cid)
                    .select_related('entrance__building__complex')
                    .order_by('entrance__building__number', 'entrance__number', 'number')
                )

    visitors = _get_visitor_queryset_for_user(user)
    if complex_obj:
        visitors = visitors.filter(apartment__entrance__building__complex=complex_obj)
    elif selected_complex and is_superadmin(user):
        try:
            cid = int(selected_complex)
        except (ValueError, TypeError):
            cid = None
        if cid is not None:
            visitors = visitors.filter(apartment__entrance__building__complex__complex_id=cid)

    try:
        selected_complex_value = int(selected_complex) if selected_complex else None
    except (ValueError, TypeError):
        selected_complex_value = None

    return render(
        request,
        'complexes/visitors_list.html',
        {
            'visitors': visitors.order_by('-created_at'),
            'form': form,
            'complex': complex_obj,
            'complexes': complexes,
            'selected_complex': selected_complex_value,
            'show_complex_column': is_superadmin(user) and not selected_complex_value,
        },
    )


@login_required
def visitor_qr(request, pk):
    visitors = _get_visitor_queryset_for_user(request.user)
    if visitors is None:
        return forbidden_response(request)

    visitor = get_object_or_404(visitors, pk=pk)

    return render(
        request,
        'complexes/visitor_qr.html',
        {
            'visitor': visitor,
            'qr_image_url': visitor.get_qr_image_url(),
        },
    )


@login_required
@require_POST
def visitor_qr_validate(request):
    visitors = _get_visitor_queryset_for_user(request.user)
    if visitors is None:
        return forbidden_response(request)

    token = (request.POST.get('token') or '').strip()
    if not token:
        return JsonResponse(
            {'valid': False, 'message': 'QR-код не передано.'},
            status=400,
        )

    try:
        visitor_id = Visitor.parse_qr_token(token)
    except signing.BadSignature:
        return JsonResponse(
            {'valid': False, 'message': 'QR-код недійсний або пошкоджений.'},
            status=400,
        )

    visitor = visitors.filter(pk=visitor_id).first()
    if visitor is None:
        return JsonResponse(
            {
                'valid': False,
                'message': 'Дозвіл не знайдено або у вас немає доступу до цього відвідувача.',
            },
            status=404,
        )

    apartment_label = '-'
    complex_name = ''
    if visitor.apartment_id:
        apartment_label = f"Кв. {visitor.apartment.number}"
        if (
            visitor.apartment.entrance_id
            and visitor.apartment.entrance.building_id
            and visitor.apartment.entrance.building.complex_id
        ):
            complex_name = visitor.apartment.entrance.building.complex.name

    return JsonResponse(
        {
            'valid': True,
            'message': 'Дозвіл підтверджено.',
            'visitor': {
                'id': visitor.pk,
                'fullname': visitor.fullname,
                'purpose': visitor.purpose or '-',
                'created_at': visitor.created_at.strftime('%Y-%m-%d %H:%M'),
                'apartment': apartment_label,
                'complex': complex_name,
                'qr_url': request.build_absolute_uri(reverse('visitor_qr', args=[visitor.pk])),
            },
        }
    )


@login_required
def resident_quick_add(request):
    if not _has_guard_access(request.user):
        return forbidden_response(request)

    staff = request.user.staff_account.staff
    complex_obj = staff.complex

    if request.method == 'POST':
        form = ResidentForm(request.POST, complex_obj=complex_obj)
        if form.is_valid():
            form.save()
            return redirect('resident_quick_add')
    else:
        form = ResidentForm(complex_obj=complex_obj)

    return render(
        request,
        'complexes/simple_form.html',
        {
            'title': 'Додати мешканця',
            'form': form,
        },
    )


@login_required
def visitor_delete(request, pk):
    visitors = _get_visitor_queryset_for_user(request.user)
    if visitors is None:
        return forbidden_response(request)

    visitor = get_object_or_404(visitors, pk=pk)

    if request.method == 'POST':
        visitor.delete()
        return redirect('visitors_list')

    return render(
        request,
        'complexes/confirm_delete.html',
        {
            'title': f'Видалити відвідувача: {visitor.fullname}?',
        },
    )
