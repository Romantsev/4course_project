from django import forms
from .models import (
    ResidentialComplex, Building, Entrance, Apartment,
    Owner, Resident, Staff, ParkingZone, ParkingSpot, StorageRoom, Visitor
)
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from .owner_compat import owner_has_complex_column, owner_matches_complex, owners_for_complex


def apartment_choice_label(apartment):
    entrance = getattr(apartment, 'entrance', None)
    building = getattr(entrance, 'building', None)
    complex_obj = getattr(building, 'complex', None)

    parts = [f"Кв. {apartment.number}"]
    if complex_obj is not None:
        parts.append(f"ЖК {complex_obj.name}")
    if building is not None:
        parts.append(f"буд. {building.number}")
    if entrance is not None:
        parts.append(f"під'їзд {entrance.number}")
    return " | ".join(parts)


def visitor_apartment_choice_label(apartment):
    entrance = getattr(apartment, 'entrance', None)
    building = getattr(entrance, 'building', None)
    complex_obj = getattr(building, 'complex', None)

    parts = []
    if complex_obj is not None:
        parts.append(f"ЖК {complex_obj.name}")
    if building is not None:
        parts.append(f"буд. {building.number}")
    if entrance is not None:
        parts.append(f"під'їзд {entrance.number}")
    parts.append(f"кв. {apartment.number}")
    return " | ".join(parts)


def entrance_choice_label(entrance):
    building = getattr(entrance, 'building', None)
    complex_obj = getattr(building, 'complex', None)

    parts = []
    if complex_obj is not None:
        parts.append(f"ЖК {complex_obj.name}")
    if building is not None:
        parts.append(f"буд. {building.number}")
    parts.append(f"під'їзд {entrance.number}")
    return " | ".join(parts)


def parking_zone_choice_label(parking_zone):
    entrance = getattr(parking_zone, 'entrance', None)
    building = getattr(entrance, 'building', None)
    complex_obj = getattr(building, 'complex', None)

    parts = []
    if complex_obj is not None:
        parts.append(f"ЖК {complex_obj.name}")
    if building is not None:
        parts.append(f"буд. {building.number}")
    if entrance is not None:
        parts.append(f"під'їзд {entrance.number}")
    parts.append(f"зона #{parking_zone.pk}")
    if parking_zone.type:
        parts.append(str(parking_zone.type))
    return " | ".join(parts)


def owner_choice_label(owner):
    parts = [owner.name]
    complex_name = None

    if owner_has_complex_column():
        complex_obj = getattr(owner, 'complex', None)
        if complex_obj is not None:
            complex_name = complex_obj.name
    else:
        apartment = (
            owner.apartments.select_related('entrance__building__complex')
            .order_by('apartment_id')
            .first()
        )
        if apartment and apartment.entrance and apartment.entrance.building and apartment.entrance.building.complex:
            complex_name = apartment.entrance.building.complex.name

    if complex_name:
        parts.append(f"ЖК {complex_name}")
    return " | ".join(parts)


def configure_apartment_field(field):
    field.queryset = field.queryset.select_related('entrance__building__complex')
    field.label_from_instance = apartment_choice_label
    return field


def configure_entrance_field(field):
    field.queryset = field.queryset.select_related('building__complex')
    field.label_from_instance = entrance_choice_label
    return field


def configure_parking_zone_field(field):
    field.queryset = field.queryset.select_related('entrance__building__complex')
    field.label_from_instance = parking_zone_choice_label
    return field


def configure_owner_field(field):
    if owner_has_complex_column():
        field.queryset = field.queryset.select_related('complex')
    field.label_from_instance = owner_choice_label
    return field

letters_validator = RegexValidator(
    r'^[A-Za-zА-Яа-яІіЇїЄєҐґʼ’\s-]+$',
    "Поле повинно містити лише букви"
)

def validate_phone_or_email(value):
    phone_validator = RegexValidator(
        r'^\+?\d+$',
        'Телефон повинен містити цифри, допускається + на початку'
    )
    email_validator = EmailValidator('Некоректний email')

    try:
        phone_validator(value) 
    except ValidationError:
        try:
            email_validator(value)  
        except ValidationError:
            raise ValidationError(
                'Введіть або номер телефону (цифри, можна з + на початку), або EMAIL'
            )


class ResidentialComplexForm(forms.ModelForm):
    class Meta:
        model = ResidentialComplex
        fields = ['name', 'address', 'management', 'contact']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад, Green Park Residence'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Місто, вулиця, будинок'
            }),
            'management': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ТОВ "Керуєм Разом"'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть телефон або email'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact'].validators = [validate_phone_or_email]




class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['number', 'floors']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'floors': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'number': 'Номер',
            'floors': 'Поверхів',
        }


class EntranceForm(forms.ModelForm):
    class Meta:
        model = Entrance
        fields = ['number']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'number': 'Номер',
        }


class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['number', 'floor', 'rooms', 'area_m2', 'owner']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'rooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'area_m2': forms.NumberInput(attrs={'class': 'form-control'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'number': 'Номер',
            'floor': 'Поверх',
            'rooms': 'Кімнат',
            'area_m2': 'Площа м²',
            'owner': 'Власник',
        }

    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)
        self.fields['owner'].required = False
        if complex_obj is not None:
            self.fields['owner'].queryset = Owner.objects.filter(
                complex=complex_obj
            ).order_by('name')



class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['name', 'phone', 'complex']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'complex': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': "Ім'я",
            'phone': 'Телефон',
        }

    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].validators = [letters_validator]
        self.fields['phone'].validators = [validate_phone_or_email]
        self.fields['complex'].label = 'ЖК'
        self.fields['complex'].required = True
        if complex_obj is not None:
            self.fields['complex'].queryset = ResidentialComplex.objects.filter(
                pk=complex_obj.pk
            )
            self.fields['complex'].initial = complex_obj


class ResidentForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = ['fullname', 'contact', 'role', 'apartment']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'fullname': 'ПІБ',
            'contact': 'Контакт',
            'role': 'Роль',
            'apartment': 'Квартира',
        }

    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)
        self.fields['fullname'].validators = [letters_validator]
        self.fields['contact'].validators = [validate_phone_or_email]
        self.fields['role'].validators = [letters_validator]
        self.fields['apartment'].required = False
        configure_apartment_field(self.fields['apartment'])

        if complex_obj is not None:
            self.fields['apartment'].queryset = Apartment.objects.filter(
                entrance__building__complex=complex_obj
            ).select_related(
                'entrance__building__complex'
            ).order_by(
                'entrance__building__number',
                'entrance__number',
                'number'
            )



class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['fullname', 'contact', 'role', 'work_schedule', 'complex']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'work_schedule': forms.TextInput(attrs={'class': 'form-control'}),
            'complex': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'fullname': 'ПІБ',
            'contact': 'Контакт',
            'role': 'Посада',
            'work_schedule': 'Графік роботи',
            'complex': 'Комплекс',
        }

    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)
        self.fields['fullname'].validators = [letters_validator]
        self.fields['contact'].validators = [validate_phone_or_email]
        self.fields['role'].validators = [letters_validator]
        if complex_obj is not None:
            from .models import ResidentialComplex as RC
            self.fields['complex'].queryset = RC.objects.filter(pk=complex_obj.pk)
            self.fields['complex'].initial = complex_obj



class ParkingZoneForm(forms.ModelForm):
    class Meta:
        model = ParkingZone
        fields = ['type', 'location', 'entrance']
        widgets = {
            'type': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'entrance': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'type': 'Тип',
            'location': 'Розташування',
            'entrance': "Під'їзд",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_entrance_field(self.fields['entrance'])


class ParkingSpotForm(forms.ModelForm):
    class Meta:
        model = ParkingSpot
        fields = ['number', 'status', 'parking_zone', 'owner']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.TextInput(attrs={'class': 'form-control'}),
            'parking_zone': forms.Select(attrs={'class': 'form-select'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'number': 'Номер',
            'status': 'Статус',
            'parking_zone': 'Паркова зона',
            'owner': 'Власник',
        }


    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)
        self.fields['owner'].queryset = owners_for_complex(
            complex_obj.pk if complex_obj is not None else None
        )
        if complex_obj is not None:
            self.fields['parking_zone'].queryset = ParkingZone.objects.filter(
                entrance__building__complex=complex_obj
            ).order_by('parking_zone_id')
        configure_parking_zone_field(self.fields['parking_zone'])
        configure_owner_field(self.fields['owner'])

    def clean(self):
        cleaned = super().clean()
        parking_zone = cleaned.get('parking_zone')
        owner = cleaned.get('owner')
        if parking_zone and owner:
            zone_complex_id = parking_zone.entrance.building.complex_id
            if not owner_matches_complex(owner, zone_complex_id):
                self.add_error('owner', 'Власник має належати до того ж ЖК, що і паркомісце.')
        return cleaned


from .models import StorageRoom
from .models import MaintenanceRequest

class StorageRoomForm(forms.ModelForm):
    class Meta:
        model = StorageRoom
        fields = ['number', 'location', 'status', 'apartment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['number'].label = 'Номер'
        self.fields['location'].label = 'Розташування'
        self.fields['status'].label = 'Статус'
        self.fields['apartment'].label = "Квартира (необов'язково)"
        configure_apartment_field(self.fields['apartment'])
        labels = {
            'number': 'Номер',
            'location': 'Розташування',
            'status': 'Статус',
            'apartment': 'Квартира (необов’язково)',
        }


class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ['fullname', 'purpose', 'apartment']
        labels = {
            'fullname': 'ПІБ відвідувача',
            'purpose': 'Мета візиту',
            'apartment': 'Квартира',
        }
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)
        self.fields['fullname'].label = 'ПІБ відвідувача'
        self.fields['purpose'].label = 'Мета візиту'
        self.fields['apartment'].label = 'Квартира'
        configure_apartment_field(self.fields['apartment'])
        self.fields['apartment'].label_from_instance = visitor_apartment_choice_label
        if complex_obj is not None:
            self.fields['apartment'].queryset = Apartment.objects.filter(
                entrance__building__complex=complex_obj
            ).select_related(
                'entrance__building__complex'
            ).order_by(
                'entrance__building__number', 'entrance__number', 'number'
            )

