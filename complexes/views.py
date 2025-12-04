# complexes/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from complexes.models import ResidentialComplex
from .models import (
    ResidentialComplex,
    Building,
    Entrance,
    Apartment,
    Owner,
    Resident,
    Staff,
    ParkingZone,
    ParkingSpot,
    StorageRoom,
)
from .forms import (
    ResidentialComplexForm,
    BuildingForm,
    EntranceForm,
    ApartmentForm,
    OwnerForm,
    ResidentForm,
    StaffForm,
    ParkingZoneForm,
    ParkingSpotForm,
    StorageRoomForm,
)
from accounts.utils import (
    is_superadmin,
    is_complex_admin,
    get_complex_for_admin,
    user_can_manage_complex,
)


def _has_technician_access(user):
    """
    Повертає True, якщо користувач – технічний працівник (maintenance staff).
    Використовується, щоб заборонити їм доступ до комор.
    """
    return (
        user.is_authenticated
        and hasattr(user, "staff_account")
        and getattr(user.staff_account, "access_type", "maintenance") == "maintenance"
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
            return HttpResponseForbidden("Тільки системний адміністратор може створювати ЖК.")
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
        return HttpResponseForbidden("Немає доступу до цього комплексу.")

    building_form = None
    if request.method == 'POST' and request.POST.get('add_building'):
        if not user_can_manage_complex(request.user, complex_obj):
            return HttpResponseForbidden("Доступ заборонено.")
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
        return HttpResponseForbidden("Немає доступу до цього комплексу.")

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
        return HttpResponseForbidden("Доступ заборонено.")
    if request.method == 'POST':
        complex_obj.delete()
        return redirect('complex_list')
    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити ЖК \u00AB{complex_obj.name}\u00BB?",
    })

def building_add(request, complex_pk):
    complex_obj = get_object_or_404(ResidentialComplex, pk=complex_pk)

    if not user_can_manage_complex(request.user, complex_obj):
        return HttpResponseForbidden("Немає доступу.")

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
        return HttpResponseForbidden("Немає доступу.")

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
        return HttpResponseForbidden("Немає доступу.")

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
        return HttpResponseForbidden("Немає доступу.")

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
        return HttpResponseForbidden("Немає доступу.")

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
        return HttpResponseForbidden("Немає доступу.")

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
        return HttpResponseForbidden("Немає доступу.")

    if request.method == 'POST':
        form = ApartmentForm(request.POST)
        if form.is_valid():
            apt = form.save(commit=False)
            apt.entrance = entrance
            apt.save()
            return redirect('complex_detail', pk=complex_pk)
    else:
        form = ApartmentForm()

    return render(request, 'complexes/simple_form.html', {
        'title': f"Додати квартиру у під'їзд {entrance.number}",
        'form': form,
    })


def apartment_edit(request, pk):
    apt = get_object_or_404(Apartment, pk=pk)
    complex_obj = apt.entrance.building.complex

    if not user_can_manage_complex(request.user, complex_obj):
        return HttpResponseForbidden("Немає доступу.")

    if request.method == 'POST':
        form = ApartmentForm(request.POST, instance=apt)
        if form.is_valid():
            form.save()
            return redirect('complex_detail', pk=complex_obj.pk)
    else:
        form = ApartmentForm(instance=apt)

    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати кв. {apt.number}",
        'form': form,
    })


def apartment_delete(request, pk):
    apt = get_object_or_404(Apartment, pk=pk)
    complex_obj = apt.entrance.building.complex

    if not user_can_manage_complex(request.user, complex_obj):
        return HttpResponseForbidden("Немає доступу.")

    if request.method == 'POST':
        apt.delete()
        return redirect('complex_detail', pk=complex_obj.pk)

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити кв. {apt.number}?",
    })


# =========================
#  ДОВІДКОВІ СПИСКИ (тільки SuperAdmin)
# =========================

def owners_list(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden("Немає доступу.")
    owners = Owner.objects.all().order_by('name')
    return render(request, 'complexes/owners_list.html', {'owners': owners})


def residents_list(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden("Немає доступу.")
    residents = Resident.objects.select_related('apartment').order_by('fullname')
    return render(request, 'complexes/residents_list.html', {'residents': residents})


def staff_list(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden("Немає доступу.")
    staff = Staff.objects.select_related('complex').order_by('fullname')
    return render(request, 'complexes/staff_list.html', {'staff_list': staff})


def parking_list(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden("Немає доступу.")
    zones = ParkingZone.objects.select_related('entrance').all()
    spots = ParkingSpot.objects.select_related('parking_zone', 'owner').all()
    zone_form = ParkingZoneForm()
    spot_form = ParkingSpotForm()
    return render(request, 'complexes/parking_list.html', {
        'zones': zones,
        'spots': spots,
        'zone_form': zone_form,
        'spot_form': spot_form,
    })


from django.shortcuts import render, redirect, get_object_or_404
from .models import StorageRoom, Apartment

def storage_list(request):

    # --- всі ЖК (буде звужено для адміна ЖК) ---
    complexes_qs = ResidentialComplex.objects.order_by('name')

    # --- вибраний ЖК із GET (для супер-адміна) ---
    selected_complex_id = request.GET.get("complex")
    if selected_complex_id:
        selected_complex_id = str(selected_complex_id)

    # --- якщо користувач адміністратор ЖК, фіксуємо його комплекс ---
    if is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if not complex_obj:
            return HttpResponseForbidden("Немає доступу.")
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
    apartments = Apartment.objects.select_related(
        'entrance', 'entrance__building'
    )

    if selected_complex_id:
        apartments = apartments.filter(
            entrance__building__complex_id=selected_complex_id
        )

    apartments = apartments.order_by(
        'entrance__building__number',
        'entrance__number',
        'number'
    )

    # — Додавання комірки —
    if request.method == 'POST':
        number = (request.POST.get('number') or '').strip()
        location = (request.POST.get('location') or '').strip()
        status = request.POST.get('status') or 'free'
        apartment_id = (request.POST.get('apartment') or '').strip()

        if number:
            storage = StorageRoom(
                number=number,
                location=location,
                status=status,
            )
            if apartment_id:
                storage.apartment_id = int(apartment_id)
            storage.save()

        # Повертаємось із збереженням параметра ЖК
        if selected_complex_id:
            return redirect(f"/storage/?complex={selected_complex_id}")
        return redirect('storage_list')

    return render(
        request,
        'complexes/storage_list.html',
        {
            'storages': storages,
            'apartments': apartments,
            'complexes': complexes,
            'selected_complex_id': selected_complex_id,
        },
    )





def storage_edit(request, pk):
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
    if is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if not complex_obj:
            return HttpResponseForbidden("Немає доступу.")
        # комірка має бути прив'язана до квартири в цьому ЖК
        if (
            not storage.apartment
            or storage.apartment.entrance.building.complex_id != complex_obj.pk
        ):
            return HttpResponseForbidden("Немає доступу.")
        selected_complex_id = complex_obj.pk
        complexes = complexes_qs.filter(pk=complex_obj.pk)
    else:
        complexes = complexes_qs
        selected_complex_id = request.POST.get('complex') or (
            storage.apartment.entrance.building.complex.pk
            if storage.apartment else None
        )

    selected_complex = None
    if selected_complex_id:
        selected_complex = ResidentialComplex.objects.filter(pk=selected_complex_id).first()

    # --- фільтруємо квартири по ЖК ---
    apartments = Apartment.objects.none()
    if selected_complex:
        apartments = (
            Apartment.objects
            .select_related('entrance', 'entrance__building')
            .filter(entrance__building__complex=selected_complex)
            .order_by('entrance__building__number', 'entrance__number', 'number')
        )

    # ====== POST SAVE ======
    if request.method == 'POST':
        storage.number = (request.POST.get('number') or '').strip()
        storage.location = (request.POST.get('location') or '').strip()
        storage.status = request.POST.get('status') or 'free'

        apt_id = request.POST.get('apartment')
        if apt_id:
            storage.apartment_id = int(apt_id)
        else:
            storage.apartment = None

        storage.save()
        return redirect('storage_list')

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
            return HttpResponseForbidden("Немає доступу.")

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
    if is_superadmin(request.user):
        pass
    else:
        complex_obj = get_complex_for_admin(request.user)
        if not complex_obj:
            return HttpResponseForbidden("Немає доступу.")
        has_apartment_in_complex = Apartment.objects.filter(
            owner=owner,
            entrance__building__complex=complex_obj,
        ).exists()
        if not has_apartment_in_complex:
            return HttpResponseForbidden("Немає доступу.")

    if request.method == 'POST':
        form = OwnerForm(request.POST, instance=owner)
        if form.is_valid():
            form.save()
            return redirect('owners_list')
    else:
        form = OwnerForm(instance=owner)

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
            return HttpResponseForbidden("Немає доступу.")
        has_apartment_in_complex = Apartment.objects.filter(
            owner=owner,
            entrance__building__complex=complex_obj,
        ).exists()
        if not has_apartment_in_complex:
            return HttpResponseForbidden("Немає доступу.")

    if request.method == 'POST':
        # Перед видаленням відв'язуємо квартири від власника,
        # щоб уникнути RestrictedError по Apartment.owner.
        Apartment.objects.filter(owner=owner).update(owner=None)
        owner.delete()
        return redirect('owners_list')

    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити власника: {owner.name}?",
    })
