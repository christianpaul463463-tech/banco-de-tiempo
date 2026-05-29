# 1. Usar una imagen oficial de Python ligera
FROM python:3.11-slim

# 2. Evitar que Python escriba archivos .pyc y asegurar que los logs salgan rápido
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Crear la carpeta de la app dentro del contenedor
WORKDIR /app

# 4. Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalar las librerías de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar todo el código del proyecto
COPY . /app/

# 7. Abrir el puerto para la aplicación
EXPOSE 8000

# 8. Comando para arrancar el servidor local
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
