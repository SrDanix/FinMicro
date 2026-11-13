# FinMicro

Plataforma web (Django) de gestión financiera para microempresarios chilenos:

- **Finanzas**: ingresos y gastos por categoría, búsqueda, catálogo de productos, importación y exportación Excel/CSV, panel con balance, alertas y recomendaciones.
- **Indicadores**: margen bruto, punto de equilibrio, ticket promedio, gastos fijos y variables, flujo de caja real versus proyectado y reporte mensual en PDF.
- **Impuestos**: IVA del mes calculado con los movimientos, calculadora de IVA y honorarios con tasas editables, y calendario de vencimientos F29/F22.
- **Proyecciones**: ingresos a 3 meses por tendencia lineal y escenarios optimista, base y pesimista.
- **Premium**: evaluador de viabilidad (VAN, TIR, payback, beneficio/costo) y asistente financiero en lenguaje natural.
- **Suscripciones**: Plan Básico gratis y Premium mensual con Khipu o Flow.cl (pagos verificados con la pasarela; simulados hasta configurar credenciales), renovación y vencimiento.
- **Cumplimiento**: consentimiento versionado de términos y privacidad, descarga y eliminación de datos (Ley 19.628) y registro de auditoría.

## Cómo ejecutarlo

Requisitos: Python 3.12 o superior.

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (en macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # opcional (en macOS/Linux: cp)
python manage.py migrate       # crea la base y carga planes y categorías
python manage.py createsuperuser   # opcional, para /admin
python manage.py runserver
```

Abre http://127.0.0.1:8000, crea una cuenta y empieza a registrar movimientos.

## Con Docker

Requiere [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up --build
```

Abre http://localhost:8000. Levanta la app y un PostgreSQL 17 (igual que producción);
los datos quedan en el volumen `finmicro_postgres`. Para AWS RDS, ver
[docs/17_base_de_datos_aws.md](docs/17_base_de_datos_aws.md).
Para detenerlo: `Ctrl+C` o `docker compose down`.

## Documentación del proyecto

Toda la documentación de análisis, diseño y seguimiento está en [`docs/`](docs/).
Comienza por el [estado frente a la carta Gantt](docs/00_estado_carta_gantt.md).
Para publicarlo en AWS Academy (EC2 + Docker + Nginx), sigue la
[guía de despliegue paso a paso](docs/18_despliegue_aws_academy.md). Respaldos, tareas
programadas, migración a PostgreSQL y pruebas de calidad: [operación](docs/19_operacion.md).
Para contribuir, lee [CONTRIBUTING.md](CONTRIBUTING.md).

## Usuarios de prueba

```bash
python manage.py crear_usuarios_prueba            # o, en Docker: docker compose exec web python manage.py crear_usuarios_prueba
```

Crea `prueba_basico` (Plan Básico con 4 meses de datos), `prueba_premium` (Premium con
datos) y `prueba_nuevo` (vacía) y muestra la contraseña al final. Si ya existen, no las toca.

## Tests

```bash
python manage.py test
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `finmicroaw/` | Configuración del proyecto (settings, urls) |
| `accounts/` | Usuario personalizado (RUT, negocio, rubro), registro y perfil |
| `subscriptions/` | Planes, suscripciones y pasarelas de pago |
| `finances/` | Categorías y movimientos |
| `taxes/` | Calculadora de IVA y honorarios |
| `projections/` | Proyección de ingresos y evaluador VAN/TIR |
| `core/` | Página de inicio e indicadores (mindicador.cl) |
| `templates/` | Plantillas HTML, una carpeta por app |
| `static/` | CSS |

> Las calculadoras son una herramienta de apoyo, no asesoría tributaria.
