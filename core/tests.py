from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Lead, PortfolioImage, PortfolioProject, Service, SiteContent


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


class ContentAdminModelsTests(TestCase):
    def test_admin_requires_login(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_contact_form_valid_submission(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Ana Gómez',
                'phone': '3001234567',
                'email': 'ana@example.com',
                'address': 'Calle 12 # 34-56',
                'message': 'Necesito información para un closet a medida.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gracias')
        self.assertEqual(Lead.objects.count(), 1)

    def test_contact_form_requires_fields(self):
        response = self.client.post(reverse('contact'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este campo es obligatorio')

    def test_contact_form_invalid_email(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Ana Gómez',
                'phone': '3001234567',
                'email': 'email-invalido',
                'message': 'Necesito información.'
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Introduce un correo electrónico válido')

    def test_contact_form_success_includes_whatsapp_link(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Ana Gómez',
                'phone': '3001234567',
                'email': 'ana@example.com',
                'address': 'Calle 12 # 34-56',
                'message': 'Necesito información para un closet a medida.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'wa.me/3117195100')
        self.assertContains(response, 'Mi%20nombre%20es%20Ana%20G%C3%B3mez')
        self.assertContains(response, 'Necesito%20informaci%C3%B3n%20para%20un%20closet%20a%20medida.')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ADMIN_EMAIL='admin@jjconstrumadera.com',
        DEFAULT_FROM_EMAIL='no-reply@jjconstrumadera.com',
    )
    def test_contact_form_sends_admin_notification_email(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Ana Gómez',
                'phone': '3001234567',
                'email': 'ana@example.com',
                'address': 'Calle 12 # 34-56',
                'message': 'Necesito información para un closet a medida.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['admin@jjconstrumadera.com'])
        self.assertIn('Nuevo contacto', email.subject)
        self.assertIn('Ana Gómez', email.body)
        self.assertIn('3001234567', email.body)
        self.assertIn('ana@example.com', email.body)
        self.assertIn('Necesito información para un closet a medida.', email.body)

    def test_portfolio_project_crud(self):
        image = SimpleUploadedFile('project.png', b'fake-image', content_type='image/png')
        project = PortfolioProject.objects.create(
            name='Cocina modular',
            description='Diseño funcional para vivienda moderna.',
            category='Residencial',
            image=image,
            is_active=True,
        )
        PortfolioImage.objects.create(project=project, image=image)

        self.assertEqual(PortfolioProject.objects.count(), 1)
        project.description = 'Nueva descripción'
        project.save()
        self.assertEqual(project.description, 'Nueva descripción')

        project.is_active = False
        project.save()
        self.assertFalse(project.is_active)

        project.delete()
        self.assertEqual(PortfolioProject.objects.count(), 0)

    def test_service_and_site_content_creation(self):
        image = SimpleUploadedFile('service.png', b'fake-image', content_type='image/png')
        service = Service.objects.create(
            name='Closets a medida',
            description='Solución de almacenamiento personalizada.',
            image=image,
            is_active=True,
        )
        content = SiteContent.objects.create(
            slug='hero-title',
            title='Soluciones a medida para espacios que marcan la diferencia.',
            body='Texto principal para la sección de inicio.',
            is_active=True,
        )

        self.assertEqual(Service.objects.count(), 1)
        self.assertEqual(SiteContent.objects.count(), 1)
        self.assertEqual(service.name, 'Closets a medida')
        self.assertEqual(content.slug, 'hero-title')

    def test_lead_crud(self):
        lead = Lead.objects.create(
            name='Ana Gómez',
            phone='3001234567',
            email='ana@example.com',
            address='Calle 12 # 34-56',
            message='Necesito una cotización para un closet.',
            status='nuevo',
        )

        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(lead.status, 'nuevo')

        lead.status = 'contactado'
        lead.admin_notes = 'Se programó llamada.'
        lead.save()
        self.assertEqual(lead.status, 'contactado')

        lead.delete()
        self.assertEqual(Lead.objects.count(), 0)
