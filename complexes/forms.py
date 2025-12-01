from django import forms
from .models import (
    ResidentialComplex, Building, Entrance, Apartment,
    Owner, Resident, Staff, ParkingZone, ParkingSpot, StorageRoom, Visitor
)
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError

letters_validator = RegexValidator(
    r'^[A-Za-zА-Яа-яІіЇїЄєҐґʼ’\s-]+$',
    "Поле повинно містити лише букви"
)

def validate_phone_or_email(value):
    phone_validator = RegexValidator(
        r'^\d+$',
        'Телефон повинен містити тільки цифри'
    )
    email_validator = EmailValidator('Некоректний email')

    try:
        phone_validator(value) 
    except ValidationError:
        try:
            email_validator(value)  
        except ValidationError:
            raise ValidationError(
                'Введіть або номер телефону (лише цифри), або EMAIL'
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
        super().__init__(*args, **kwargs)
        self.fields['owner'].required = False



class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': "Ім'я",
            'phone': 'Телефон',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].validators = [letters_validator]
        self.fields['phone'].validators = [validate_phone_or_email]


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

        if complex_obj is not None:
            self.fields['apartment'].queryset = Apartment.objects.filter(
                entrance__building__complex=complex_obj
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
        if complex_obj is not None:
            self.fields['apartment'].queryset = Apartment.objects.filter(
                entrance__building__complex=complex_obj
            ).order_by(
                'entrance__building__number', 'entrance__number', 'number'
            )

