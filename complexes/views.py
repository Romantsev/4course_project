# complexes/views.py

from django.contrib import messages
from django.db.models import Prefetch, Q
from residence_manager.responses import forbidden_response
from django.shortcuts import get_object_or_404, redirect, render
from .models import (
    ResidentialComplex,
    Building,
    Entrance,
    Apartment,
    Owner,
    Staff,
    StorageRoom,
)
from .forms import (
    ResidentialComplexForm,
    BuildingForm,
    EntranceForm,
    ApartmentForm,
    OwnerForm,
)
from accounts.utils import (
    is_superadmin,
    is_complex_admin,
    get_complex_for_admin,
    user_can_manage_complex,
)



def _has_storage_access(user):
    return is_superadmin(user) or is_complex_admin(user)


def _storage_redirect(selected_complex_id=None):
    if selected_complex_id:
        return redirect(f"/storage/?complex={selected_complex_id}")
    return redirect('storage_list')


def _get_storage_apartments(selected_complex_id=None):
    apartments = Apartment.objects.select_related(
        'entrance', 'entrance__building', 'entrance__building__complex'
    )
    if selected_complex_id:
        apartments = apartments.filter(
            entrance__building__complex_id=selected_complex_id
        )
    return apartments.order_by(
        'entrance__building__number',
        'entrance__number',
        'number',
    )


# =========================
#  ГОЛОВНА: СПИСОК ЖК
# =========================

def complex_list(request):
    """
    Головна сторінка:
    - показує всі ЖК
    - супер адмін може створити новий ЖК (форма внизу)
    """
    q = (request.GET.get('q') or '').strip()
    complexes = ResidentialComplex.objects.all().order_by('name')
    if q:
        complexes = complexes.filter(Q(name__icontains=q) | Q(address__icontains=q))

    if request.method == 'POST':
        if not is_superadmin(request.user):
            return forbidden_response(request)
        form = ResidentialComplexForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('complex_list')
    else:
        form = ResidentialComplexForm()

    return render(request, 'complexes/complex_list.html', {
        'complexes': complexes,
        'form': form,
        'q': q,
    })


# =========================
#  ДЕТАЛІ ЖК
# =========================

def complex_detail(request, pk):
    """
    Детальна сторінка одного ЖК.
    Доступ:
    - SuperAdmin
    - ComplexAdmin для цього ЖК
    - (опційно тільки перегляд можна буде відкрити ширше)
    """
    complex_obj = get_object_or_404(ResidentialComplex, pk=pk)

    if not user_can_manage_complex(request.user, complex_obj) and not is_superadmin(request.user):
        return forbidden_response(request)

    building_form = None
    if request.method == 'POST' and request.POST.get('add_building'):
        if not user_can_manage_complex(request.user, complex_obj):
            return forbidden_response(request)
        building_form = BuildingForm(request.POST)
        if building_form.is_valid():
            b = building_form.save(commit=False)
            b.complex = complex_obj
            b.save()
            return redirect('complex_detail', pk=complex_obj.pk)

    buildings = (
        Building.objects.filter(complex=complex_obj)
        .prefetch_related(
            Prefetch(
                'entrances',
                queryset=Entrance.objects.prefetch_related(
                    Prefetch(
                        'apartments',
                        queryset=Apartment.objects.select_related('owner')
                    )
                )
            )
        )
        .order_by('number')
    )

    staff = Staff.objects.filter(complex=complex_obj).order_by('fullname')

    return render(request, 'complexes/complex_detail.html', {
        'complex': complex_obj,
        'buildings': buildings,
        'staff': staff,
        'building_form': building_form or BuildingForm(),
    })


def complex_edit(request, pk):
    """
    Редагування даних ЖК.
    Доступ: SuperAdmin або ComplexAdmin цього комплексу.
    """
    complex_obj = get_object_or_404(ResidentialComplex, pk=pk)

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        form = ResidentialComplexForm(request.POST, instance=complex_obj)
        if form.is_valid():
            form.save()
            return redirect('complex_detail', pk=complex_obj.pk)
    else:
        form = ResidentialComplexForm(instance=complex_obj)

    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати ЖК «{complex_obj.name}»",
        'form': form,
    })


# =========================
#  БУДИНКИ
# =========================

def complex_delete(request, pk):
    complex_obj = get_object_or_404(ResidentialComplex, pk=pk)
    if not is_superadmin(request.user):
        return forbidden_response(request)
    if request.method == 'POST':
        complex_obj.delete()
        return redirect('complex_list')
    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити ЖК \u00AB{complex_obj.name}\u00BB?",
    })

def building_add(request, complex_pk):
    complex_obj = get_object_or_404(ResidentialComplex, pk=complex_pk)

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        form = BuildingForm(request.POST)
        if form.is_valid():
            b = form.save(commit=False)
            b.complex = complex_obj
            b.save()
            return redirect('complex_detail', pk=complex_pk)
    else:
        form = BuildingForm()

    return render(request, 'complexes/simple_form.html', {
        'title': f"Додати будинок у {complex_obj.name}",
        'form': form,
    })


def building_edit(request, pk):
    building = get_object_or_404(Building, pk=pk)
    complex_obj = building.complex

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        form = BuildingForm(request.POST, instance=building)
        if form.is_valid():
            form.save()
            return redirect('complex_detail', pk=complex_obj.pk)
    else:
        form = BuildingForm(instance=building)

    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати будинок {building.number}",
        'form': form,
    })


def building_delete(request, pk):
    building = get_object_or_404(Building, pk=pk)
    complex_obj = building.complex

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        building.delete()
        return redirect('complex_detail', pk=complex_obj.pk)

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити будинок {building.number}?",
    })


# =========================
#  ПІД'ЇЗДИ
# =========================

def entrance_add(request, complex_pk, building_id):
    complex_obj = get_object_or_404(ResidentialComplex, pk=complex_pk)
    building = get_object_or_404(Building, pk=building_id, complex=complex_obj)

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        form = EntranceForm(request.POST)
        if form.is_valid():
            e = form.save(commit=False)
            e.building = building
            e.save()
            return redirect('complex_detail', pk=complex_pk)
    else:
        form = EntranceForm()

    return render(request, 'complexes/simple_form.html', {
        'title': f"Додати під'їзд до будинку {building.number}",
        'form': form,
    })


def entrance_edit(request, pk):
    entrance = get_object_or_404(Entrance, pk=pk)
    complex_obj = entrance.building.complex

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        form = EntranceForm(request.POST, instance=entrance)
        if form.is_valid():
            form.save()
            return redirect('complex_detail', pk=complex_obj.pk)
    else:
        form = EntranceForm(instance=entrance)

    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати під'їзд {entrance.number}",
        'form': form,
    })


def entrance_delete(request, pk):
    entrance = get_object_or_404(Entrance, pk=pk)
    complex_obj = entrance.building.complex

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        entrance.delete()
        return redirect('complex_detail', pk=complex_obj.pk)

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити під'їзд {entrance.number}?",
    })


# =========================
#  КВАРТИРИ
# =========================

def entrance_add_apartment(request, complex_pk, entrance_id):
    complex_obj = get_object_or_404(ResidentialComplex, pk=complex_pk)
    entrance = get_object_or_404(Entrance, pk=entrance_id, building__complex=complex_obj)

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        form = ApartmentForm(request.POST, complex_obj=complex_obj)
        if form.is_valid():
            apt = form.save(commit=False)
            apt.entrance = entrance
            apt.save()
            return redirect('complex_detail', pk=complex_pk)
    else:
        form = ApartmentForm(complex_obj=complex_obj)

    return render(request, 'complexes/simple_form.html', {
        'title': f"Додати квартиру у під'їзд {entrance.number}",
        'form': form,
    })


def apartment_edit(request, pk):
    apt = get_object_or_404(Apartment, pk=pk)
    complex_obj = apt.entrance.building.complex

    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        form = ApartmentForm(request.POST, instance=apt, complex_obj=complex_obj)
        if form.is_valid():
            form.save()
            return redirect('complex_detail', pk=complex_obj.pk)
    else:
        form = ApartmentForm(instance=apt, complex_obj=complex_obj)

    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати кв. {apt.number}",
        'form': form,
    })


def apartment_delete(request, pk):
    apt = get_object_or_404(Apartment, pk=pk)
    complex_obj = apt.entrance.building.complex

    # Видаляти квартири може супер-адмін або адміністратор цього ЖК
    if not user_can_manage_complex(request.user, complex_obj):
        return forbidden_response(request)

    if request.method == 'POST':
        apt.delete()
        return redirect('complex_detail', pk=complex_obj.pk)

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити кв. {apt.number}?",
    })

def storage_list(request):
    if not _has_storage_access(request.user):
        return forbidden_response(request)


    # --- всі ЖК (буде звужено для адміна ЖК) ---
    complexes_qs = ResidentialComplex.objects.order_by('name')

    # --- вибраний ЖК із GET (для супер-адміна) ---
    selected_complex_id = (request.GET.get("complex") or "").strip() or None

    # --- якщо користувач адміністратор ЖК, фіксуємо його комплекс ---
    if is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if not complex_obj:
            return forbidden_response(request)
        selected_complex_id = str(complex_obj.pk)
        complexes = complexes_qs.filter(pk=complex_obj.pk)
    else:
        complexes = complexes_qs

    # --- базовий queryset ---
    storages = StorageRoom.objects.select_related(
        'apartment',
        'apartment__entrance',
        'apartment__entrance__building',
        'apartment__entrance__building__complex'
    ).order_by('number')

    # --- фільтр за ЖК ---
    if selected_complex_id:
        storages = storages.filter(
            apartment__entrance__building__complex_id=selected_complex_id
        )

    # — квартири для форми додавання —
    apartments = _get_storage_apartments(selected_complex_id)

    # — Додавання комірки —
    if request.method == 'POST':
        number = (request.POST.get('number') or '').strip()
        location = (request.POST.get('location') or '').strip()
        status = request.POST.get('status') or 'free'
        apartment_id = (request.POST.get('apartment') or '').strip()

        apartment = None
        error_message = None
        if not number:
            error_message = "Номер комірки є обов'язковим."
        elif apartment_id:
            apartment = apartments.filter(pk=apartment_id).first()
            if apartment is None:
                error_message = "Квартира має належати вибраному ЖК."
        elif selected_complex_id:
            error_message = "Для комірки в межах ЖК потрібно вибрати квартиру."

        if error_message:
            messages.error(request, error_message)
        else:
            StorageRoom.objects.create(
                number=number,
                location=location,
                status=status,
                apartment=apartment,
            )

        # Повертаємось із збереженням параметра ЖК
            return _storage_redirect(selected_complex_id)

    return render(
        request,
        'complexes/storage_list.html',
        {
            'storages': storages,
            'apartments': apartments,
            'complexes': complexes,
            'selected_complex_id': selected_complex_id,
            'show_complex_column': is_superadmin(request.user) and not selected_complex_id,
        },
    )
def storage_edit(request, pk):
    if not _has_storage_access(request.user):
        return forbidden_response(request)

    storage = get_object_or_404(
        StorageRoom.objects.select_related(
            'apartment',
            'apartment__entrance',
            'apartment__entrance__building',
            'apartment__entrance__building__complex'
        ),
        pk=pk
    )

    # --- всі ЖК (буде звужено для адміна ЖК) ---
    complexes_qs = ResidentialComplex.objects.order_by('name')

    # --- перевірка доступу та поточний ЖК ---
    selected_complex_id = None
    selected_complex = None
    if is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if not complex_obj:
            return forbidden_response(request)
        # комірка має бути прив'язана до квартири в цьому ЖК
        if (
            not storage.apartment
            or storage.apartment.entrance.building.complex_id != complex_obj.pk
        ):
            return forbidden_response(request)
        selected_complex_id = str(complex_obj.pk)
        complexes = complexes_qs.filter(pk=complex_obj.pk)
        selected_complex = complex_obj
    else:
        complexes = complexes_qs
        selected_complex_id = (request.GET.get('complex') or '').strip() or (
            request.POST.get('complex') or ''
        ).strip() or (
            str(storage.apartment.entrance.building.complex.pk)
            if storage.apartment else None
        )
        if selected_complex_id:
            selected_complex = ResidentialComplex.objects.filter(pk=selected_complex_id).first()

    # --- фільтруємо квартири по ЖК ---
    apartments = _get_storage_apartments(selected_complex_id) if selected_complex_id else _get_storage_apartments()

    # ====== POST SAVE ======
    if request.method == 'POST':
        storage.number = (request.POST.get('number') or '').strip()
        storage.location = (request.POST.get('location') or '').strip()
        storage.status = request.POST.get('status') or 'free'

        apartment_id = (request.POST.get('apartment') or '').strip()
        apartment = None
        error_message = None
        if not storage.number:
            error_message = "Номер комірки є обов'язковим."
        elif apartment_id:
            apartment = apartments.filter(pk=apartment_id).first()
            if apartment is None:
                error_message = "Квартира має належати вибраному ЖК."
        elif selected_complex_id:
            error_message = "Для комірки в межах ЖК потрібно вибрати квартиру."

        if error_message:
            messages.error(request, error_message)
        else:
            storage.apartment = apartment
            storage.save()
            return _storage_redirect(selected_complex_id)

    return render(
        request,
        'complexes/storage_edit.html',
        {
            'storage': storage,
            'complexes': complexes,
            'selected_complex': selected_complex,
            'apartments': apartments,
        },
    )


def storage_delete(request, pk):
    if not _has_storage_access(request.user):
        return forbidden_response(request)

    storage = get_object_or_404(
        StorageRoom.objects.select_related(
            'apartment',
            'apartment__entrance',
            'apartment__entrance__building',
            'apartment__entrance__building__complex',
        ),
        pk=pk,
    )

    # --- доступ для адміна ЖК тільки до свого комплексу ---
    if is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if (
            not complex_obj
            or not storage.apartment
            or storage.apartment.entrance.building.complex_id != complex_obj.pk
        ):
            return forbidden_response(request)

    if request.method == 'POST':
        storage.delete()
        return redirect('storage_list')
    return render(
        request,
        'complexes/confirm_delete.html',
        {
            'title': f"Видалити комірку №{storage.number}?",
        },
    )


def owner_edit(request, pk):
    """
    Редагування власника.
    Доступ: SuperAdmin або ComplexAdmin власного ЖК.
    """
    owner = Owner.objects.filter(pk=pk).first()
    if not owner:
        messages.warning(request, "Власника не знайдено або вже видалено.")
        return redirect('owners_list')

    # Перевірка прав
    form_kwargs = {}
    if is_superadmin(request.user):
        pass
    else:
        complex_obj = get_complex_for_admin(request.user)
        if not complex_obj:
            return forbidden_response(request)
        form_kwargs['complex_obj'] = complex_obj
        if owner.complex_id != complex_obj.pk:
            return forbidden_response(request)

    if request.method == 'POST':
        form = OwnerForm(request.POST, instance=owner, **form_kwargs)
        if form.is_valid():
            form.save()
            return redirect('owners_list')
    else:
        form = OwnerForm(instance=owner, **form_kwargs)

    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати власника: {owner.name}",
        'form': form,
    })


def owner_delete(request, pk):
    """
    Видалення власника.
    Доступ: SuperAdmin або ComplexAdmin власного ЖК.
    """
    owner = Owner.objects.filter(pk=pk).first()
    if not owner:
        messages.warning(request, "Власника не знайдено або вже видалено.")
        return redirect('owners_list')

    # Перевірка прав
    if is_superadmin(request.user):
        pass
    else:
        complex_obj = get_complex_for_admin(request.user)
        if not complex_obj:
            return forbidden_response(request)
        if owner.complex_id != complex_obj.pk:
            return forbidden_response(request)

    if request.method == 'POST':
        # Перед видаленням відв'язуємо квартири від власника,
        # щоб уникнути RestrictedError по Apartment.owner.
        Apartment.objects.filter(owner=owner).update(owner=None)
        owner.delete()
        return redirect('owners_list')

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити власника: {owner.name}?",
    })
