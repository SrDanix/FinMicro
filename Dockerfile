# ---------------------------------------------------------------
# Imagen de FinMicro. Cada línea es un "paso" (capa) de la receta.
# ---------------------------------------------------------------

# 1. Imagen base: un Linux mínimo que ya trae Python instalado.
FROM python:3.13-slim

# 2. Ajustes de Python: no crear archivos .pyc y mostrar los logs al instante.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Carpeta de trabajo dentro del contenedor (como hacer "cd /app").
WORKDIR /app

# 4. Instalar dependencias. Se copia SOLO requirements.txt primero para que
#    Docker reutilice esta capa mientras no cambien las dependencias
#    (las siguientes construcciones serán mucho más rápidas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código (lo que excluye .dockerignore no entra).
COPY . .

# 6. Juntar los archivos estáticos (CSS) en /app/staticfiles para WhiteNoise.
RUN DJANGO_DEBUG=False python manage.py collectstatic --noinput

# 7. Por seguridad, la app no corre como administrador (root).
RUN useradd --create-home finmicro && mkdir -p /app/data && chown -R finmicro /app
USER finmicro

# 8. Puerto en el que escucha la app dentro del contenedor.
EXPOSE 8000

# 9. Al arrancar: aplicar migraciones y levantar Gunicorn (servidor de producción).
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn finmicroaw.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
