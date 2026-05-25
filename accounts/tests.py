import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from accounts.models import (
    Role, Client, Category, Service, TimeAccount,
    Request as ServiceRequest, TimeTransaction, Review, Report
)
from accounts.forms import UserRegistrationForm, ProfileEditForm

class ModelStringRepresentationTests(TestCase):
    def test_role_str(self):
        """Valida la representación en cadena de un objeto Role."""
        role = Role.objects.create(role_name='test_role', role_description='Desc')
        self.assertEqual(str(role), 'test_role')

    def test_category_str(self):
        """Valida la representación en cadena de un objeto Category."""
        cat = Category.objects.create(category_name='test_category', category_description='Desc')
        self.assertEqual(str(cat), 'test_category')

class BasicViewsTests(TestCase):
    def test_home_view(self):
        """Valida el renderizado correcto de la vista HomeView."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_servicios_recientes_view(self):
        """Valida el renderizado de la vista de servicios recientes."""
        response = self.client.get(reverse('servicios_recientes'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Aún no hay servicios recientes.', response.content.decode())

class HU001RegistroTests(TestCase):
    def setUp(self):
        self.role_usuario = Role.objects.create(role_name='usuario', role_description='Usuario estándar')
        
    def test_registration_form_fields(self):
        """Valida que el formulario de registro falle con campos vacíos o email inválido."""
        form_data = {
            'first_name': '',
            'last_name': 'Perez',
            'email': 'invalid-email',
            'username': 'juanperez',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('email', form.errors)

    def test_successful_registration_assigns_role(self):
        """Valida que el registro exitoso asigne automáticamente el rol de 'usuario'."""
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'juan@example.com',
            'username': 'juanperez',
            'password1': 'password123!',
            'password2': 'password123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.role, self.role_usuario)

    def test_registration_creates_time_account(self):
        """Valida que la creación del usuario dispare la creación automática de una TimeAccount."""
        client = Client.objects.create_user(username='test_user', password='password123')
        self.assertTrue(TimeAccount.objects.filter(client=client).exists())
        time_account = client.time_account
        self.assertEqual(float(time_account.balance_hours), 5.00)

    def test_username_validation_available(self):
        """Valida la verificación de HTMX para un nombre de usuario disponible."""
        response = self.client.post(reverse('validar_username'), {'username': 'new_user'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nombre de usuario disponible.')

    def test_username_validation_taken(self):
        """Valida la verificación de HTMX para un nombre de usuario ya en uso."""
        Client.objects.create_user(username='taken_user', password='password123')
        response = self.client.post(reverse('validar_username'), {'username': 'taken_user'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este nombre de usuario ya está en uso.')

    def test_username_validation_empty(self):
        """Valida la verificación de HTMX cuando el nombre de usuario está vacío."""
        response = self.client.post(reverse('validar_username'), {'username': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '')

    def test_successful_registration_redirect_and_login(self):
        """Valida que el registro exitoso inicie sesión y redirija al usuario al dashboard."""
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'juan@example.com',
            'username': 'juanperez',
            'password1': 'password123!',
            'password2': 'password123!',
        }
        response = self.client.post(reverse('register'), data=form_data)
        self.assertRedirects(response, reverse('dashboard'))
        self.assertIn('_auth_user_id', self.client.session)
        
        client = Client.objects.get(username='juanperez')
        self.assertEqual(client.role, self.role_usuario)

    def test_registration_without_role_does_not_fail(self):
        """Valida que el registro no falle si el rol 'usuario' no existe en la base de datos."""
        self.role_usuario.delete()
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'juan@example.com',
            'username': 'juanperez2',
            'password1': 'password123!',
            'password2': 'password123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertIsNone(user.role)

class HU002LoginTests(TestCase):
    def setUp(self):
        self.user = Client.objects.create_user(username='test_user', password='password123', email='test@example.com')

    def test_login_successful(self):
        """Valida que el inicio de sesión con credenciales correctas redirija al dashboard."""
        response = self.client.post(reverse('login'), {'username': 'test_user', 'password': 'password123'})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_invalid_credentials(self):
        """Valida que el inicio de sesión con credenciales inválidas muestre un error de formulario."""
        response = self.client.post(reverse('login'), {'username': 'test_user', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_login_inactive_user(self):
        """Valida que un usuario inactivo no pueda iniciar sesión."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse('login'), {'username': 'test_user', 'password': 'password123'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

class HU003DashboardTests(TestCase):
    def setUp(self):
        self.user = Client.objects.create_user(username='test_user', password='password123')
        self.other_user = Client.objects.create_user(username='other_user', password='password123')
        self.category = Category.objects.create(category_name='Educación', category_description='Clases y tutorías')
        
        self.my_service = Service.objects.create(client=self.user, category=self.category, title='Mi servicio', description='Desc', estimated_time=2.00, status='active')
        self.other_services = []
        for i in range(8):
            s = Service.objects.create(client=self.other_user, category=self.category, title=f'Servicio {i}', description='Desc', estimated_time=1.00, status='active')
            self.other_services.append(s)
            
        self.inactive_service = Service.objects.create(client=self.other_user, category=self.category, title='Inactivo', description='Desc', estimated_time=1.00, status='inactive')

    def test_dashboard_requires_login(self):
        """Valida que el dashboard redirija a la página de login si el usuario no está autenticado."""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/login/?next=/dashboard/')

    def test_dashboard_context_authenticated(self):
        """Valida que el dashboard contenga los datos correctos del usuario autenticado en su contexto."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        context = response.context
        
        self.assertEqual(context['my_services_count'], 1)
        self.assertEqual(float(context['time_account'].balance_hours), 5.00)
        self.assertEqual(context['pending_requests_count'], 0)
        
        recent_services = list(context['recent_services'])
        self.assertEqual(len(recent_services), 6)
        self.assertNotIn(self.my_service, recent_services)
        self.assertNotIn(self.inactive_service, recent_services)
        self.assertEqual(recent_services[0], self.other_services[-1])

    def test_dashboard_active_requests_context(self):
        """Valida que el dashboard contenga las solicitudes activas de servicios en el contexto."""
        req1 = ServiceRequest.objects.create(
            service=self.my_service,
            requester_client=self.other_user,
            provider_client=self.user,
            requested_hours=2.00,
            request_status='pending'
        )
        req2 = ServiceRequest.objects.create(
            service=self.other_services[0],
            requester_client=self.user,
            provider_client=self.other_user,
            requested_hours=1.00,
            request_status='accepted'
        )
        req3 = ServiceRequest.objects.create(
            service=self.other_services[1],
            requester_client=self.user,
            provider_client=self.other_user,
            requested_hours=1.00,
            request_status='completed'
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        active_requests = list(response.context['active_requests'])
        self.assertEqual(len(active_requests), 2)
        self.assertIn(req1, active_requests)
        self.assertIn(req2, active_requests)
        self.assertNotIn(req3, active_requests)

class HU004ServicePublicationTests(TestCase):
    def setUp(self):
        self.user = Client.objects.create_user(username='test_user', password='password123')
        self.category = Category.objects.create(category_name='Clases', category_description='Desc')

    def test_create_service_requires_login(self):
        """Valida que la creación de servicios requiera que el usuario esté autenticado."""
        response = self.client.get(reverse('service_create'))
        self.assertRedirects(response, '/login/?next=/servicios/crear/')
        
        response_post = self.client.post(reverse('service_create'), {
            'title': 'Clases de Python',
            'category': self.category.pk,
            'description': 'Aprende Python',
            'estimated_time': '3.00'
        })
        self.assertRedirects(response_post, '/login/?next=/servicios/crear/')

    def test_create_service_authenticated_success(self):
        """Valida la publicación exitosa de un nuevo servicio para un usuario autenticado."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('service_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('categories', response.context)
        
        post_data = {
            'title': 'Clases de Django',
            'category': self.category.pk,
            'description': 'Aprende Django',
            'estimated_time': '2.50',
            'status': 'active'
        }
        response_post = self.client.post(reverse('service_create'), post_data)
        self.assertRedirects(response_post, reverse('service_list'))
        
        self.assertEqual(Service.objects.count(), 1)
        srv = Service.objects.first()
        self.assertEqual(srv.title, 'Clases de Django')
        self.assertEqual(srv.client, self.user)
        self.assertEqual(srv.category, self.category)
        self.assertEqual(float(srv.estimated_time), 2.50)
        self.assertEqual(srv.status, 'active')

class IntegracionRegistroLoginDashboardTest(TestCase):
    def test_flujo_registro_login_dashboard(self):
        """Valida el flujo de integración de un nuevo usuario desde el registro, pasando por el inicio de sesión, hasta acceder al dashboard principal."""
        role_usuario = Role.objects.create(role_name='usuario', role_description='Usuario estándar')
        
        form_data = {
            'first_name': 'Carlos',
            'last_name': 'Gomez',
            'email': 'carlos@example.com',
            'username': 'carlosgomez',
            'password1': 'TestingPass123!',
            'password2': 'TestingPass123!',
        }
        response = self.client.post(reverse('register'), data=form_data)
        
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(Client.objects.filter(username='carlosgomez').exists())
        user = Client.objects.get(username='carlosgomez')
        self.assertEqual(user.role, role_usuario)
        
        self.assertTrue(hasattr(user, 'time_account'))
        
        login_response = self.client.post(reverse('login'), {
            'username': 'carlosgomez',
            'password': 'TestingPass123!'
        })
        
        self.assertEqual(login_response.status_code, 302)
        self.assertRedirects(login_response, reverse('dashboard'))
        
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)

class IntegracionCrearServicioTest(TestCase):
    def setUp(self):
        self.role_usuario = Role.objects.create(role_name='usuario', role_description='Usuario estándar')
        self.category = Category.objects.create(category_name='Mantenimiento', category_description='Reparaciones del hogar')
        self.user = Client.objects.create_user(username='testuser', password='password123', role=self.role_usuario)

    def test_flujo_crear_y_explorar_servicio(self):
        """Valida el flujo de integración donde un usuario autenticado publica un servicio y este es visible en las búsquedas y el explorador."""
        self.client.force_login(self.user)
        
        post_data = {
            'title': 'Plomería rápida',
            'description': 'Reparación de griferías y tuberías con experiencia.',
            'category': self.category.pk,
            'estimated_time': '2.00',
        }
        response = self.client.post(reverse('service_create'), post_data)
        
        self.assertRedirects(response, reverse('service_list'))
        
        self.assertTrue(Service.objects.filter(title='Plomería rápida').exists())
        srv = Service.objects.get(title='Plomería rápida')
        self.assertEqual(srv.status, 'active')
        self.assertEqual(srv.client, self.user)
        
        list_response = self.client.get(reverse('service_list'))
        self.assertEqual(list_response.status_code, 200)
        
        search_response = self.client.get(reverse('search_services'), {'q': 'Plomería'})
        self.assertEqual(search_response.status_code, 200)
        self.assertContains(search_response, 'Plomería rápida')

class IntegracionSolicitarYAceptarServicioTest(TestCase):
    def setUp(self):
        self.role_usuario = Role.objects.create(role_name='usuario', role_description='Usuario estándar')
        self.category = Category.objects.create(category_name='Idiomas', category_description='Clases de lenguas')
        
        self.solicitante = Client.objects.create_user(username='solicitante', password='password123', role=self.role_usuario)
        self.proveedor = Client.objects.create_user(username='proveedor', password='password123', role=self.role_usuario)
        
        self.sol_account = self.solicitante.time_account
        self.sol_account.balance_hours = 10.00
        self.sol_account.save()
        
        self.prov_account = self.proveedor.time_account
        self.prov_account.balance_hours = 10.00
        self.prov_account.save()
        
        self.service = Service.objects.create(
            client=self.proveedor,
            category=self.category,
            title='Clases de Francés',
            description='Aprende francés conversacional.',
            estimated_time=2.00,
            status='active'
        )

    def test_flujo_solicitar_aceptar_transferencia_horas(self):
        """Valida el flujo de integración donde un usuario solicita un servicio, el proveedor lo acepta, las horas se transfieren correctamente y se genera la transacción correspondiente."""
        self.client.force_login(self.solicitante)
        
        post_data = {
            'requested_hours': '2.00',
            'request_message': 'Me gustaría tomar una clase de conversación.'
        }
        request_response = self.client.post(reverse('request_service', args=[self.service.pk]), post_data)
        
        self.assertEqual(request_response.status_code, 200)
        
        self.assertEqual(ServiceRequest.objects.count(), 1)
        req = ServiceRequest.objects.first()
        self.assertEqual(req.service, self.service)
        self.assertEqual(req.requester_client, self.solicitante)
        self.assertEqual(req.provider_client, self.proveedor)
        self.assertEqual(req.request_status, 'pending')
        self.assertEqual(float(req.requested_hours), 2.00)
        
        self.sol_account.refresh_from_db()
        self.assertEqual(float(self.sol_account.balance_hours), 8.00)
        
        self.client.force_login(self.proveedor)
        
        accept_response = self.client.post(reverse('accept_request', args=[req.pk]))
        
        self.assertEqual(accept_response.status_code, 200)
        
        req.refresh_from_db()
        self.assertEqual(req.request_status, 'accepted')
        
        self.prov_account.refresh_from_db()
        self.assertEqual(float(self.prov_account.balance_hours), 12.00)
        
        self.assertTrue(TimeTransaction.objects.filter(request=req).exists())
        tx = TimeTransaction.objects.get(request=req)
        self.assertEqual(tx.sender_client, self.solicitante)
        self.assertEqual(tx.receiver_client, self.proveedor)
        self.assertEqual(float(tx.hours_amount), 2.00)
        self.assertEqual(tx.transaction_type, 'transfer')
































class HU011UserReportsTests(TestCase):
    def setUp(self):
        self.reporter = Client.objects.create_user(username='reporter', password='password123')
        self.reported = Client.objects.create_user(username='reported', password='password123')
        self.category = Category.objects.create(category_name='Clases', category_description='Desc')
        self.srv = Service.objects.create(client=self.reported, category=self.category, title='Clases', description='Desc', estimated_time=2.00, status='active')
        self.service_req = ServiceRequest.objects.create(
            service=self.srv, requester_client=self.reporter, provider_client=self.reported, requested_hours=2.00, request_status='accepted'
        )

    def test_report_self_prevented(self):
        """Valida que un usuario no pueda reportarse a sí mismo."""
        self.client.force_login(self.reporter)
        response = self.client.post(reverse('report_create', args=[self.reporter.pk]), {
            'report_reason': 'Autoreporte',
            'report_description': 'Me porto mal'
        })
        self.assertRedirects(response, reverse('service_list'))
        self.assertEqual(Report.objects.count(), 0)

    def test_report_creation_success(self):
        """Valida la creación exitosa de un reporte sobre otro usuario."""
        self.client.force_login(self.reporter)
        response = self.client.get(reverse('report_create', args=[self.reported.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['reported_client'], self.reported)
        self.assertIn(self.service_req, response.context['related_requests'])

        post_data = {
            'report_reason': 'Incumplimiento',
            'report_description': 'No se presento a la reunion pactada.',
            'request_id': self.service_req.pk
        }
        response_post = self.client.post(reverse('report_create', args=[self.reported.pk]), post_data)
        self.assertRedirects(response_post, reverse('dashboard'))
        
        self.assertEqual(Report.objects.count(), 1)
        rep = Report.objects.first()
        self.assertEqual(rep.reporter_client, self.reporter)
        self.assertEqual(rep.reported_client, self.reported)
        self.assertEqual(rep.request, self.service_req)
        self.assertEqual(rep.report_reason, 'Incumplimiento')
        self.assertEqual(rep.report_description, 'No se presento a la reunion pactada.')
        self.assertEqual(rep.report_status, 'open')

    def test_report_duplicate_prevented(self):
        """Valida que no se pueda reportar a un usuario si ya hay un reporte abierto o en revisión."""
        Report.objects.create(
            reporter_client=self.reporter,
            reported_client=self.reported,
            report_reason='Abuso',
            report_description='Desc',
            report_status='open'
        )
        
        self.client.force_login(self.reporter)
        response = self.client.post(reverse('report_create', args=[self.reported.pk]), {
            'report_reason': 'Otro motivo',
            'report_description': 'Otra desc'
        })
        self.assertRedirects(response, reverse('service_list'))
        self.assertEqual(Report.objects.count(), 1)

class HU012AdminPanelTests(TestCase):
    def setUp(self):
        self.role_admin = Role.objects.create(role_name='administrador', role_description='Administrador')
        self.role_user = Role.objects.create(role_name='usuario', role_description='Usuario regular')
        
        self.admin = Client.objects.create_user(username='admin', password='password123', role=self.role_admin)
        self.user = Client.objects.create_user(username='user', password='password123', role=self.role_user)
        self.reported = Client.objects.create_user(username='reported', password='password123', role=self.role_user)
        
        self.report = Report.objects.create(
            reporter_client=self.user,
            reported_client=self.reported,
            report_reason='Abuso',
            report_description='Mal comportamiento',
            report_status='open'
        )
        self.cat = Category.objects.create(category_name='Clases', category_description='Desc')

    def test_admin_panel_access_denied_for_anonymous(self):
        """Valida que el panel de administración deniegue el acceso a usuarios anónimos."""
        response = self.client.get(reverse('admin_panel'))
        self.assertRedirects(response, reverse('home'))

    def test_admin_panel_access_denied_for_regular_user(self):
        """Valida que el panel de administración deniegue el acceso a usuarios sin rol de administrador."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('admin_panel'))
        self.assertRedirects(response, reverse('home'))

    def test_admin_panel_access_allowed_for_admin(self):
        """Valida el acceso correcto al panel de administración para un administrador."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('open_reports', response.context)
        self.assertIn('categories', response.context)

    def test_admin_change_report_status_unauthorized(self):
        """Valida la denegación de cambios en reportes a usuarios no autorizados."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('admin_change_report_status', args=[self.report.pk, 'under_review']))
        self.assertEqual(response.status_code, 401)

    def test_admin_change_report_status_invalid_method(self):
        """Valida que el cambio de estado de reporte rechace métodos diferentes a POST."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_change_report_status', args=[self.report.pk, 'under_review']))
        self.assertEqual(response.status_code, 405)

    def test_admin_change_report_status_under_review(self):
        """Valida el cambio exitoso de estado de un reporte a 'under_review'."""
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin_change_report_status', args=[self.report.pk, 'under_review']))
        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 'under_review')
        self.assertIn('HX-Trigger', response)

    def test_admin_change_report_status_resolved_deactivates_user(self):
        """Valida que al resolver un reporte se desactive el usuario reportado."""
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin_change_report_status', args=[self.report.pk, 'resolved']))
        self.assertEqual(response.status_code, 200)
        
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 'resolved')
        self.assertIsNotNone(self.report.resolved_at)
        
        self.reported.refresh_from_db()
        self.assertFalse(self.reported.is_active)

    def test_admin_change_report_status_dismissed(self):
        """Valida el desestimado de un reporte manteniendo al usuario activo."""
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin_change_report_status', args=[self.report.pk, 'dismissed']))
        self.assertEqual(response.status_code, 200)
        
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 'dismissed')
        self.assertIsNotNone(self.report.resolved_at)
        
        self.reported.refresh_from_db()
        self.assertTrue(self.reported.is_active)

    def test_admin_category_list_unauthorized(self):
        """Valida la denegación de visualización de categorías a usuarios no autorizados."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('admin_category_list'))
        self.assertEqual(response.status_code, 401)

    def test_admin_category_list_success(self):
        """Valida la obtención correcta de la tabla de categorías por parte del administrador."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('categories', response.context)

    def test_admin_create_category_success(self):
        """Valida la creación exitosa de una nueva categoría de servicio."""
        response = self.client.post(reverse('admin_create_category'), {
            'category_name': 'Hogar y Jardin',
            'category_description': 'Servicios de jardineria y limpieza'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.count(), 2)
        new_cat = Category.objects.get(category_name='Hogar y Jardin')
        self.assertEqual(new_cat.category_description, 'Servicios de jardineria y limpieza')

    def test_admin_create_category_invalid_method(self):
        """Valida la denegación de creación de categorías mediante peticiones no POST."""
        response = self.client.get(reverse('admin_create_category'))
        self.assertEqual(response.status_code, 405)

    def test_admin_delete_category_success(self):
        """Valida la eliminación exitosa de una categoría no utilizada."""
        response = self.client.delete(reverse('admin_delete_category', args=[self.cat.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '')
        self.assertFalse(Category.objects.filter(pk=self.cat.pk).exists())

    def test_admin_delete_category_in_use_fails(self):
        """Valida que la eliminación de una categoría en uso retorne un mensaje de error."""
        Service.objects.create(
            client=self.user,
            category=self.cat,
            title='Servicio en categoria',
            description='Desc',
            estimated_time=1.00,
            status='active'
        )
        response = self.client.delete(reverse('admin_delete_category', args=[self.cat.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: Categoría en uso.", response.content.decode())
        self.assertTrue(Category.objects.filter(pk=self.cat.pk).exists())

    def test_admin_delete_category_invalid_method(self):
        """Valida la denegación de eliminación de categorías mediante peticiones no DELETE."""
        response = self.client.post(reverse('admin_delete_category', args=[self.cat.pk]))
        self.assertEqual(response.status_code, 405)