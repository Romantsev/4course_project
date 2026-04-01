from accounts.forms import OwnerAccountCreateForm
from accounts.models import OwnerAccount
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from complexes.forms import OwnerForm
from complexes.models import Owner, ResidentialComplex


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
