# JJ Construmadera Web

Proyecto base en Django para JJ Construmadera SAS.

## Requisitos

- Python 3.13+
- pip
- Entorno virtual recomendado

## Instalación local

1. Crear un entorno virtual:
   ```bash
   py -m venv .venv
   ```
2. Activar el entorno:
   ```bash
   .\.venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
4. Copiar variables de entorno:
   ```bash
   copy .env.example .env
   ```
5. Ajustar los valores en `.env` si es necesario.
6. Ejecutar migraciones:
   ```bash
   python manage.py migrate
   ```
7. Iniciar el servidor:
   ```bash
   python manage.py runserver
   ```

La aplicación estará disponible en:

- http://127.0.0.1:8000/

## Configuración de base de datos

Por defecto, el proyecto usa SQLite para desarrollo. Para producción, cambie `USE_SQLITE=False` en `.env` y complete las variables PostgreSQL.

## Estructura principal

- `construmadera_web/`: configuración central del proyecto
- `core/`: aplicación base para la home y lógica inicial
- `templates/`: plantillas globales
- `static/`: archivos estáticos
- `media/`: archivos multimedia
