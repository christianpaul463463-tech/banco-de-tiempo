# TimeConnect - Plataforma de Banco de Tiempo ⏳

## Descripción del Proyecto
TimeConnect es una aplicación web basada en el concepto de "Banco de Tiempo", diseñada para que los miembros de una comunidad puedan intercambiar servicios, habilidades y conocimientos utilizando el **tiempo (horas)** como la única moneda de cambio. Si prestas una hora de tu tiempo enseñando algo, ganas una hora de crédito para consumir un servicio de otro usuario de la comunidad.

## Arquitectura General del Sistema
El proyecto está desarrollado bajo el patrón arquitectónico **Monolítico**, utilizando la estructura **MVT (Model-View-Template)** propia del framework Django.
* **Backend y Lógica de Negocio:** Python 3.11 con Django Framework (rutas, controladores/vistas y modelos ORM).
* **Frontend:** Templates HTML nativos de Django, potenciados con Tailwind CSS / CSS tradicional y renderizado dinámico en el servidor.
* **Base de Datos:** SQLite para el entorno de desarrollo local y PostgreSQL para producción.

## Tecnologías Utilizadas
* **Lenguaje principal:** Python 3.11
* **Framework Web:** Django
* **Contenedores:** Docker y Docker Compose (Entorno de aprendizaje local)
* **Integración Continua:** GitHub Actions
* **Plataforma de Despliegue:** Render / Railway

---

## Instrucciones para Ejecutar el Proyecto Localmente

### Opción 1: Ejecución tradicional con Python

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/christianpaul463463-tech/banco-de-tiempo.git](https://github.com/christianpaul463463-tech/banco-de-tiempo.git)
   cd banco-de-tiempo
2. Crear y activar un entorno virtual:
   python -m venv venv
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
3. Instalar las dependencias del sistema:
pip install -r requirements.txt
4. Aplicar las migraciones a la Base de Datos:
python manage.py migrate
5. Iniciar el servidor de desarrollo:
python manage.py runserver
6. Abre en tu navegador la dirección: http://127.0.0.1:8000
Opción 2: Ejecución automatizada con Docker
Si dispones de Docker instalado en tu máquina, puedes desplegar el entorno completo corriendo el siguiente comando en la raíz del repositorio:
docker-compose up --build
Una vez finalice, la aplicación estará disponible en http://127.0.0.1:8000.

   
