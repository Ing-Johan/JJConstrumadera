from django.test import TestCase
from django.urls import reverse


class PublicPagesTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_services_page_loads(self):
        response = self.client.get(reverse('services'))
        self.assertEqual(response.status_code, 200)

    def test_portfolio_page_loads(self):
        response = self.client.get(reverse('portfolio'))
        self.assertEqual(response.status_code, 200)

    def test_about_page_loads(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_contact_page_loads(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
