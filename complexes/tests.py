from accounts.forms import OwnerAccountCreateForm
from accounts.models import OwnerAccount
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from complexes.forms import OwnerForm, ParkingSpotForm
from complexes.models import Building, Entrance, Owner, ParkingZone, ResidentialComplex


User = get_user_model()


class StorageAccessTests(TestCase):
    def _forbidden_urls(self):
        return [
            reverse('storage_list'),
            reverse('storage_edit', args=[1]),
            reverse('storage_delete', args=[1]),
            reverse('visitors_list'),
        ]

    def test_protected_endpoints_forbid_anonymous_user(self):
        for url in self._forbidden_urls():
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 403)


class OwnerBindingTests(TestCase):
    def test_owner_form_requires_complex(self):
        form = OwnerForm(data={'name': 'Owner Test', 'phone': '123456'})

        self.assertFalse(form.is_valid())
        self.assertIn('complex', form.errors)

    def test_owner_form_accepts_phone_with_country_code_prefix(self):
        complex_one = ResidentialComplex.objects.create(name='A', address='Addr A')

        form = OwnerForm(
            data={
                'name': 'Owner Test',
                'phone': '+380669093322',
                'complex': complex_one.pk,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_owner_form_limits_complex_for_complex_admin_flow(self):
        complex_one = ResidentialComplex.objects.create(name='A', address='Addr A')
        complex_two = ResidentialComplex.objects.create(name='B', address='Addr B')

        form = OwnerForm(complex_obj=complex_one)

        self.assertEqual(list(form.fields['complex'].queryset), [complex_one])
        self.assertEqual(form.fields['complex'].initial, complex_one)
        self.assertNotIn(complex_two, form.fields['complex'].queryset)

    def test_owner_account_form_uses_owner_complex_binding(self):
        complex_one = ResidentialComplex.objects.create(name='A', address='Addr A')
        complex_two = ResidentialComplex.objects.create(name='B', address='Addr B')
        owner_allowed = Owner.objects.create(name='Allowed', complex=complex_one)
        owner_other = Owner.objects.create(name='Other', complex=complex_two)
        owner_with_account = Owner.objects.create(name='Taken', complex=complex_one)
        user = User.objects.create_user(username='taken', password='pass12345')
        OwnerAccount.objects.create(user=user, owner=owner_with_account)

        form = OwnerAccountCreateForm(complex_obj=complex_one)

        self.assertIn(owner_allowed, form.fields['owner'].queryset)
        self.assertNotIn(owner_other, form.fields['owner'].queryset)
        self.assertNotIn(owner_with_account, form.fields['owner'].queryset)

    def test_storage_endpoints_forbid_authenticated_non_admin_user(self):
        user = User.objects.create_user(username='user', password='pass12345')
        self.client.force_login(user)

        for url in [
            reverse('storage_list'),
            reverse('storage_edit', args=[1]),
            reverse('storage_delete', args=[1]),
        ]:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 403)


class ParkingSpotFormTests(TestCase):
    def setUp(self):
        self.complex_one = ResidentialComplex.objects.create(name='A', address='Addr A')
        self.complex_two = ResidentialComplex.objects.create(name='B', address='Addr B')
        building = Building.objects.create(number=1, floors=9, complex=self.complex_one)
        entrance = Entrance.objects.create(number=1, building=building)
        self.zone = ParkingZone.objects.create(type='indoor', location='L1', entrance=entrance)
        self.owner_allowed = Owner.objects.create(name='Allowed Owner', complex=self.complex_one)
        self.owner_other = Owner.objects.create(name='Other Owner', complex=self.complex_two)

    def test_parking_spot_form_limits_owners_to_current_complex(self):
        form = ParkingSpotForm(complex_obj=self.complex_one)

        self.assertIn(self.owner_allowed, form.fields['owner'].queryset)
        self.assertNotIn(self.owner_other, form.fields['owner'].queryset)

    def test_parking_spot_form_rejects_owner_from_other_complex(self):
        form = ParkingSpotForm(
            data={
                'number': 1,
                'status': 'active',
                'parking_zone': self.zone.pk,
                'owner': self.owner_other.pk,
            },
            complex_obj=self.complex_one,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('owner', form.errors)
