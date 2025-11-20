from django import forms
from django.contrib.auth import get_user_model
from complexes.models import ResidentialComplex, Owner, Staff
from .models import ComplexAdminProfile, OwnerAccount, StaffAccount

User = get_user_model()


class BaseUserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Підтвердження пароля",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Паролі не співпадають.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ComplexAdminCreateForm(BaseUserCreateForm):
    complex = forms.ModelChoiceField(
        queryset=ResidentialComplex.objects.all(),
        label="Житловий комплекс",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class OwnerAccountCreateForm(BaseUserCreateForm):
    owner = forms.ModelChoiceField(
        queryset=Owner.objects.none(),
        label="Власник",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)

        qs = Owner.objects.filter(account__isnull=True)
        if complex_obj:
            qs = qs.filter(
                apartments__entrance__building__complex=complex_obj
            ).distinct()
        self.fields['owner'].queryset = qs


class StaffAccountCreateForm(BaseUserCreateForm):
    staff = forms.ModelChoiceField(
        queryset=Staff.objects.none(),
        label="Співробітник",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        complex_obj = kwargs.pop('complex_obj', None)
        super().__init__(*args, **kwargs)

        qs = Staff.objects.filter(account__isnull=True)
        if complex_obj:
            qs = qs.filter(complex=complex_obj)
        self.fields['staff'].queryset = qs
        self.fields['access_type'] = forms.ChoiceField(
            choices=StaffAccount.ACCESS_CHOICES,
            label='Права доступу',
            widget=forms.Select(attrs={'class': 'form-select'})
        )


# ===== Update forms =====

class BaseUserUpdateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
    )
    password2 = forms.CharField(
        label="Повторіть пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if (p1 or p2) and p1 != p2:
            self.add_error('password2', "Паролі не співпадають.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get('password1')
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user


class ComplexAdminUpdateForm(BaseUserUpdateForm):
    complex = forms.ModelChoiceField(
        queryset=ResidentialComplex.objects.all(),
        label="Житловий комплекс",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if self.profile is not None:
            self.fields['complex'].initial = self.profile.complex

    def save(self, commit=True):
        user = super().save(commit=commit)
        if self.profile is not None:
            self.profile.complex = self.cleaned_data['complex']
            if commit:
                self.profile.save()
        return user


class OwnerAccountUpdateForm(BaseUserUpdateForm):
    pass


class StaffAccountUpdateForm(BaseUserUpdateForm):
    pass
