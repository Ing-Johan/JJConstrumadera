from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Lead, PageVisit, PortfolioCategory, PortfolioImage, PortfolioProject, Service, SiteContent


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

        self.assertEqual(response.status_code, 302)
        self.assertIn('wa.me/3117195100', response.url)
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

        self.assertEqual(response.status_code, 302)
        self.assertIn('wa.me/3117195100', response.url)
        self.assertIn('Mi%20nombre%20es%20Ana%20G%C3%B3mez', response.url)
        self.assertIn('Necesito%20informaci%C3%B3n%20para%20un%20closet%20a%20medida.', response.url)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ADMIN_EMAIL='admin@jjconstrumadera.com',
        DEFAULT_FROM_EMAIL='no-reply@jjconstrumadera.com',
    )
    def test_contact_form_does_not_send_admin_notification_email(self):
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

        self.assertEqual(response.status_code, 302)
        self.assertIn('wa.me/3117195100', response.url)
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_analytics_dashboard(self):
        PageVisit.objects.create(path='/', device_type='pc')
        PageVisit.objects.create(path='/', device_type='mobile')
        PageVisit.objects.create(path='/servicios/', device_type='mobile')
        Lead.objects.create(
            name='Ana Gómez',
            phone='3001234567',
            email='ana@example.com',
            address='Calle 12 # 34-56',
            message='Necesito información.',
            status='nuevo',
        )
        Lead.objects.create(
            name='Pedro Ruiz',
            phone='3012345678',
            email='pedro@example.com',
            address='Carrera 4',
            message='Otra solicitud.',
            status='contactado',
        )
        Lead.objects.create(
            name='Luisa Gómez',
            phone='3023456789',
            email='luisa@example.com',
            address='Avenida 9',
            message='Necesito presupuesto.',
            status='cerrado',
        )

        user = get_user_model().objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='secret123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse('admin_analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visitas totales')
        self.assertContains(response, 'Leads nuevos')
        self.assertContains(response, 'Leads contactados')
        self.assertContains(response, 'Leads cerrados')
        self.assertContains(response, '3')

    def test_owner_login_page_loads(self):
        response = self.client.get(reverse('owner_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar sesión')

    def test_owner_dashboard_requires_staff(self):
        user = get_user_model().objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='secret123',
            is_staff=False,
        )
        self.client.force_login(user)
        response = self.client.get(reverse('owner_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_owner_custom_editor_dashboard_uses_own_routes(self):
        user = get_user_model().objects.create_user(
            username='ownereditor',
            email='owner@example.com',
            password='secret123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse('owner_content_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar sitio')
        self.assertNotContains(response, '/admin/')

    def test_owner_portfolio_management_page_loads(self):
        user = get_user_model().objects.create_user(
            username='portfoliomanager',
            email='portfolio@example.com',
            password='secret123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse('owner_portfolio_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Portafolio')

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

    def test_portfolio_categories_are_managed_with_custom_panel(self):
        user = get_user_model().objects.create_user(
            username='portfoliocategorymanager',
            email='category@example.com',
            password='secret123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        PortfolioCategory.objects.create(name='Cocinas', slug='cocinas', sort_order=1)

        response = self.client.get(reverse('owner_portfolio_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cocinas')
        self.assertNotContains(response, '/admin/')

    def test_public_portfolio_uses_categories_and_projects(self):
        category = PortfolioCategory.objects.create(name='Cocinas', slug='cocinas', sort_order=1)
        PortfolioProject.objects.create(
            name='Cocina moderna',
            description='Diseño premium para vivienda.',
            category=category.name,
            image=None,
            is_active=True,
        )

        response = self.client.get(reverse('portfolio'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cocinas')
        self.assertContains(response, 'Cocina moderna')

    def test_public_portfolio_project_detail_shows_images(self):
        category = PortfolioCategory.objects.create(name='Cocinas', slug='cocinas', sort_order=1)
        project = PortfolioProject.objects.create(
            name='Cocina moderna',
            description='Diseño premium para vivienda.',
            category=category.name,
            image=None,
            is_active=True,
        )
        image = SimpleUploadedFile('gallery.png', b'fake-image', content_type='image/png')
        PortfolioImage.objects.create(project=project, image=image, caption='Isla central', sort_order=1)

        response = self.client.get(reverse('portfolio_detail', args=[project.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cocina moderna')
        self.assertContains(response, 'Isla central')

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
