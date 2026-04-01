from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
