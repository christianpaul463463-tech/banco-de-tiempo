from django.core.management.base import BaseCommand
from accounts.models import Role, Category, Client, Service

class Command(BaseCommand):
    help = 'Seed initial data for TimeConnect platform'

    def handle(self, *args, **kwargs):
        # 1. Roles
        Role.objects.get_or_create(role_name='usuario', defaults={'role_description': 'Usuario estándar de la plataforma'})
        Role.objects.get_or_create(role_name='administrador', defaults={'role_description': 'Administrador del sistema'})
        
        # 2. Categorías
        categorias = ['Idiomas', 'Tecnología', 'Arte y Diseño', 'Cocina', 'Deportes y Fitness', 'Tutorías Académicas', 'Música', 'Fotografía', 'Reparaciones del Hogar', 'Salud y Bienestar']
        for cat in categorias:
            Category.objects.get_or_create(category_name=cat, defaults={'category_description': f'Categoría de {cat}'})

        # 3. Usuarios de prueba
        usuarios = [
            {'username': 'ana_martinez', 'first_name': 'Ana', 'last_name': 'Martínez', 'email': 'ana@test.com', 'phone': '3001234567', 'biography': 'Profesora de inglés con 5 años de experiencia', 'location': 'Bogotá'},
            {'username': 'carlos_perez', 'first_name': 'Carlos', 'last_name': 'Pérez', 'email': 'carlos@test.com', 'phone': '3009876543', 'biography': 'Desarrollador web full stack, especialista en Python', 'location': 'Medellín'},
            {'username': 'lucia_gomez', 'first_name': 'Lucía', 'last_name': 'Gómez', 'email': 'lucia@test.com', 'phone': '3015551234', 'biography': 'Diseñadora gráfica y fotógrafa aficionada', 'location': 'Cali'},
            {'username': 'miguel_torres', 'first_name': 'Miguel', 'last_name': 'Torres', 'email': 'miguel@test.com', 'phone': '3027778899', 'biography': 'Chef aficionado, me encanta enseñar recetas colombianas', 'location': 'Bogotá'},
            {'username': 'sofia_rodriguez', 'first_name': 'Sofía', 'last_name': 'Rodríguez', 'email': 'sofia@test.com', 'phone': '3033334455', 'biography': 'Estudiante de música, toco guitarra y piano', 'location': 'Barranquilla'},
            {'username': 'juan_lopez', 'first_name': 'Juan', 'last_name': 'López', 'email': 'juan@test.com', 'phone': '3041112233', 'biography': 'Entrenador personal certificado', 'location': 'Bogotá'},
            {'username': 'valentina_cruz', 'first_name': 'Valentina', 'last_name': 'Cruz', 'email': 'valentina@test.com', 'phone': '3056667788', 'biography': 'Matemática y tutora universitaria', 'location': 'Medellín'},
            {'username': 'andres_mora', 'first_name': 'Andrés', 'last_name': 'Mora', 'email': 'andres@test.com', 'phone': '3069990011', 'biography': 'Técnico en reparación de electrodomésticos', 'location': 'Cali'},
        ]
        
        user_role = Role.objects.get(role_name='usuario')
        admin_role = Role.objects.get(role_name='administrador')
        
        created_users = 0
        for u in usuarios:
            client, created = Client.objects.get_or_create(username=u['username'], defaults={
                'first_name': u['first_name'],
                'last_name': u['last_name'],
                'email': u['email'],
                'phone': u['phone'],
                'biography': u['biography'],
                'location': u['location'],
                'role': user_role
            })
            if created:
                client.set_password('timeconnect123')
                client.save()
                
                # El TimeAccount ya se crea por el signal, le ajustamos el balance
                if hasattr(client, 'time_account'):
                    client.time_account.balance_hours = 10.00
                    client.time_account.save()
                    
                created_users += 1

        # 4. Administrador de prueba
        admin, admin_created = Client.objects.get_or_create(username='admin_tc', defaults={
            'first_name': 'Admin',
            'last_name': 'TimeConnect',
            'email': 'admin@timeconnect.com',
            'role': admin_role,
            'is_staff': True,
            'is_superuser': True
        })
        if admin_created:
            admin.set_password('admin123')
            admin.save()

        # 5. Servicios de prueba
        servicios = [
            {'client': 'ana_martinez', 'categoria': 'Idiomas', 'title': 'Clases de inglés conversacional', 'description': 'Te ayudo a mejorar tu inglés conversacional con sesiones dinámicas y prácticas. Adaptamos el ritmo a tu nivel actual, desde básico hasta intermedio-avanzado.', 'estimated_time': 1.5},
            {'client': 'carlos_perez', 'categoria': 'Tecnología', 'title': 'Ayuda con Python y Django', 'description': 'Te asesoro en proyectos de Python, Django, APIs REST o cualquier duda de programación. Puedo ayudarte a resolver bugs, entender conceptos o revisar tu código.', 'estimated_time': 2.0},
            {'client': 'lucia_gomez', 'categoria': 'Arte y Diseño', 'title': 'Diseño de logo o imagen de marca', 'description': 'Creo logotipos y elementos visuales para tu proyecto personal o emprendimiento. Entrego archivos en PNG, JPG y PDF. Incluye hasta 2 revisiones.', 'estimated_time': 3.0},
            {'client': 'miguel_torres', 'categoria': 'Cocina', 'title': 'Taller de cocina tradicional colombiana', 'description': 'Aprende a preparar platos típicos colombianos como bandeja paisa, ajiaco o sancocho. Sesión práctica desde la comodidad de tu cocina o la mía.', 'estimated_time': 2.5},
            {'client': 'sofia_rodriguez', 'categoria': 'Música', 'title': 'Clases de guitarra para principiantes', 'description': 'Enseño guitarra acústica desde cero. En pocas sesiones aprenderás acordes básicos y podrás tocar tus primeras canciones. Paciencia garantizada.', 'estimated_time': 1.0},
            {'client': 'juan_lopez', 'categoria': 'Deportes y Fitness', 'title': 'Rutina de ejercicios personalizada', 'description': 'Diseño una rutina de ejercicios adaptada a tus objetivos y nivel físico. Incluye calentamiento, ejercicios principales y enfriamiento. Puedo hacer seguimiento por una semana.', 'estimated_time': 1.5},
            {'client': 'valentina_cruz', 'categoria': 'Tutorías Académicas', 'title': 'Tutoría de cálculo y álgebra lineal', 'description': 'Explico cálculo diferencial, integral y álgebra lineal de forma clara y con ejercicios prácticos. Ideal para estudiantes universitarios que necesitan refuerzo.', 'estimated_time': 2.0},
            {'client': 'andres_mora', 'categoria': 'Reparaciones del Hogar', 'title': 'Reparación de electrodomésticos pequeños', 'description': 'Reparo licuadoras, planchas, ventiladores, cargadores y otros electrodomésticos de uso doméstico. Diagnóstico sin costo, solo pagas si se puede reparar.', 'estimated_time': 1.5},
        ]
        
        created_services = 0
        for s in servicios:
            client = Client.objects.filter(username=s['client']).first()
            category = Category.objects.filter(category_name=s['categoria']).first()
            if client and category:
                service, s_created = Service.objects.get_or_create(
                    client=client, 
                    title=s['title'],
                    defaults={
                        'category': category,
                        'description': s['description'],
                        'estimated_time': s['estimated_time']
                    }
                )
                if s_created:
                    created_services += 1

        # Salida
        self.stdout.write("=== Datos de prueba generados para TimeConnect ===")
        self.stdout.write("* 2 roles creados/verificados")
        self.stdout.write("* 10 categorías creadas/verificadas")
        self.stdout.write(f"* {created_users} usuarios de prueba creados (contraseña: timeconnect123)")
        self.stdout.write(f"* {'1' if admin_created else '0'} administrador creado (usuario: admin_tc, contraseña: admin123)")
        self.stdout.write(f"* {created_services} servicios de prueba creados")
        self.stdout.write("")
        self.stdout.write("Credenciales rápidas:")
        self.stdout.write("Usuario: ana_martinez / timeconnect123")
        self.stdout.write("Admin: admin_tc / admin123")
        self.stdout.write("==========================================")
