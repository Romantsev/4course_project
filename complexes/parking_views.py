from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden

from .models import ParkingZone, ParkingSpot, Entrance, ResidentialComplex
from .forms import ParkingZoneForm, ParkingSpotForm
from accounts.utils import is_superadmin, is_complex_admin, get_complex_for_admin


def parking_list(request):
    complexes = ResidentialComplex.objects.order_by('name')
    selected_complex_id = (request.GET.get('complex') or '').strip()

    if is_superadmin(request.user):
        if request.method == 'POST':
            if request.POST.get('add_zone'):
                zone_form = ParkingZoneForm(request.POST)
                spot_form = ParkingSpotForm()
                if zone_form.is_valid():
                    zone_form.save()
                    if selected_complex_id:
                        return redirect(f"{request.path}?complex={selected_complex_id}")
                    return redirect('parking_list')
            elif request.POST.get('add_spot'):
                spot_form = ParkingSpotForm(request.POST)
                zone_form = ParkingZoneForm()
                if spot_form.is_valid():
                    spot_form.save()
                    if selected_complex_id:
                        return redirect(f"{request.path}?complex={selected_complex_id}")
                    return redirect('parking_list')
            else:
                zone_form = ParkingZoneForm()
                spot_form = ParkingSpotForm()
        else:
            zone_form = ParkingZoneForm()
            spot_form = ParkingSpotForm()

        zones = ParkingZone.objects.select_related(
            'entrance__building__complex'
        ).all()
        spots = ParkingSpot.objects.select_related(
            'parking_zone__entrance__building__complex',
            'owner',
        ).all()

        if selected_complex_id:
            try:
                cid = int(selected_complex_id)
            except (TypeError, ValueError):
                cid = None
            if cid is not None:
                zones = zones.filter(entrance__building__complex_id=cid)
                spots = spots.filter(parking_zone__entrance__building__complex_id=cid)

                if zone_form is not None:
                    zone_form.fields['entrance'].queryset = Entrance.objects.filter(
                        building__complex_id=cid
                    ).order_by('building__number', 'number')
                if spot_form is not None:
                    spot_form.fields['parking_zone'].queryset = ParkingZone.objects.filter(
                        entrance__building__complex_id=cid
                    ).order_by('parking_zone_id')

    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if complex_obj is None:
            return HttpResponseForbidden("Доступ заборонено.")

        # фіксований ЖК для адміністратора
        selected_complex_id = str(complex_obj.pk)
        complexes = ResidentialComplex.objects.filter(pk=complex_obj.pk)

        zones = ParkingZone.objects.select_related(
            'entrance__building__complex'
        ).filter(
            entrance__building__complex=complex_obj
        )
        spots = ParkingSpot.objects.select_related(
            'parking_zone__entrance__building__complex',
            'owner',
        ).filter(
            parking_zone__entrance__building__complex=complex_obj
        )

        # форми додавання зон/місць
        if request.method == 'POST':
            if request.POST.get('add_zone'):
                zone_form = ParkingZoneForm(request.POST)
                spot_form = ParkingSpotForm()
            elif request.POST.get('add_spot'):
                spot_form = ParkingSpotForm(request.POST)
                zone_form = ParkingZoneForm()
            else:
                zone_form = ParkingZoneForm()
                spot_form = ParkingSpotForm()
        else:
            zone_form = ParkingZoneForm()
            spot_form = ParkingSpotForm()

        # обмежуємо вибір лише об'єктами поточного ЖК
        entrances_qs = Entrance.objects.filter(
            building__complex=complex_obj
        ).order_by('building__number', 'number')
        zones_qs = ParkingZone.objects.filter(
            entrance__building__complex=complex_obj
        ).order_by('parking_zone_id')

        if zone_form is not None:
            zone_form.fields['entrance'].queryset = entrances_qs
        if spot_form is not None:
            spot_form.fields['parking_zone'].queryset = zones_qs

        if request.method == 'POST':
            if request.POST.get('add_zone') and zone_form.is_valid():
                zone_form.save()
                return redirect('parking_list')
            if request.POST.get('add_spot') and spot_form.is_valid():
                spot_form.save()
                return redirect('parking_list')
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    return render(request, 'complexes/parking_list.html', {
        'zones': zones,
        'spots': spots,
        'zone_form': zone_form,
        'spot_form': spot_form,
        'complexes': complexes,
        'selected_complex_id': selected_complex_id,
    })


def parking_zone_edit(request, pk):
    zone = get_object_or_404(
        ParkingZone.objects.select_related('entrance__building__complex'),
        pk=pk,
    )

    complex_obj = None
    if is_superadmin(request.user):
        pass
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if (
            complex_obj is None
            or zone.entrance.building.complex_id != complex_obj.pk
        ):
            return HttpResponseForbidden("Доступ заборонено.")
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    if request.method == 'POST':
        form = ParkingZoneForm(request.POST, instance=zone)
        if complex_obj is not None:
            form.fields['entrance'].queryset = Entrance.objects.filter(
                building__complex=complex_obj
            ).order_by('building__number', 'number')
        if form.is_valid():
            form.save()
            return redirect('parking_list')
    else:
        form = ParkingZoneForm(instance=zone)
        if complex_obj is not None:
            form.fields['entrance'].queryset = Entrance.objects.filter(
                building__complex=complex_obj
            ).order_by('building__number', 'number')
    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати паркінг-зону #{zone.parking_zone_id}",
        'form': form,
    })


def parking_zone_delete(request, pk):
    zone = get_object_or_404(
        ParkingZone.objects.select_related('entrance__building__complex'),
        pk=pk,
    )

    if is_superadmin(request.user):
        pass
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if (
            complex_obj is None
            or zone.entrance.building.complex_id != complex_obj.pk
        ):
            return HttpResponseForbidden("Доступ заборонено.")
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    if request.method == 'POST':
        zone.delete()
        return redirect('parking_list')
    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити паркінг-зону #{zone.parking_zone_id}?",
    })


def parking_spot_edit(request, pk):
    spot = get_object_or_404(
        ParkingSpot.objects.select_related(
            'parking_zone__entrance__building__complex'
        ),
        pk=pk,
    )

    complex_obj = None
    if is_superadmin(request.user):
        pass
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if (
            complex_obj is None
            or spot.parking_zone.entrance.building.complex_id != complex_obj.pk
        ):
            return HttpResponseForbidden("Доступ заборонено.")
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    if request.method == 'POST':
        form = ParkingSpotForm(request.POST, instance=spot)
        if complex_obj is not None:
            form.fields['parking_zone'].queryset = ParkingZone.objects.filter(
                entrance__building__complex=complex_obj
            ).order_by('parking_zone_id')
        if form.is_valid():
            form.save()
            return redirect('parking_list')
    else:
        form = ParkingSpotForm(instance=spot)
        if complex_obj is not None:
            form.fields['parking_zone'].queryset = ParkingZone.objects.filter(
                entrance__building__complex=complex_obj
            ).order_by('parking_zone_id')
    return render(request, 'complexes/simple_form.html', {
        'title': f"Редагувати паркомісце №{spot.number}",
        'form': form,
    })


def parking_spot_delete(request, pk):
    spot = get_object_or_404(
        ParkingSpot.objects.select_related(
            'parking_zone__entrance__building__complex'
        ),
        pk=pk,
    )

    if is_superadmin(request.user):
        pass
    elif is_complex_admin(request.user):
        complex_obj = get_complex_for_admin(request.user)
        if (
            complex_obj is None
            or spot.parking_zone.entrance.building.complex_id != complex_obj.pk
        ):
            return HttpResponseForbidden("Доступ заборонено.")
    else:
        return HttpResponseForbidden("Доступ заборонено.")

    if request.method == 'POST':
        spot.delete()
        return redirect('parking_list')
    return render(request, 'complexes/confirm_delete.html', {
        'title': f"Видалити паркомісце №{spot.number}?",
    })
