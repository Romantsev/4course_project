from django import forms
from .models import MaintenanceRequest, Apartment


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['apartment', 'description']
        widgets = {
            'apartment': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Опишіть проблему...'}),
        }

    def __init__(self, *args, **kwargs):
        owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.fields['apartment'].queryset = Apartment.objects.filter(owner=owner)
        self.fields['apartment'].label = 'Квартира'
        self.fields['description'].label = 'Опис проблеми'

