# FinMicro

Plataforma web (Django) de gestión financiera para microempresarios chilenos:

- **Finanzas**: registro de ingresos y gastos por categoría, panel con balance del mes y gráfico de 6 meses.
- **Impuestos**: calculadora de IVA (19%) y retención de boletas de honorarios (tasas Ley 21.133).
- **Proyecciones**: proyección de ingresos a 3 meses por tendencia lineal.
- **Evaluador de viabilidad** (Premium): VAN, TIR, payback y beneficio/costo.
- **Suscripciones**: Plan Básico gratis y Premium, con pago simulado (Khipu / Flow.cl) hasta configurar credenciales reales.

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

Abre http://localhost:8000. Los datos quedan en el volumen `finmicro_datos`.
Para detenerlo: `Ctrl+C` o `docker compose down`.

## Documentación del proyecto

Toda la documentación de análisis, diseño y seguimiento está en [`docs/`](docs/).
Comienza por el [estado frente a la carta Gantt](docs/00_estado_carta_gantt.md).
Para contribuir, lee [CONTRIBUTING.md](CONTRIBUTING.md).

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
