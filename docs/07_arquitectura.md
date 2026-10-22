# Arquitectura (modelo C4) y stack tecnológico

**Actividades 3.3 y 3.5** · Responsable: Danilo · Aprueba: Carlos · Semanas 6–7

Arquitectura MVP: **monolito modular en Django sobre una sola instancia EC2**, empaquetado
en Docker. Se eligió por costo (cabe en el presupuesto de la actividad 6.0) y porque un
equipo de cuatro personas puede operarlo. El camino para crecer está en
[08_plan_escalamiento.md](08_plan_escalamiento.md).

## Nivel 1 — Contexto

```mermaid
flowchart LR
    U["👤 Microempresario<br/>Registra ventas y gastos,<br/>calcula impuestos"]
    C["👤 Colaborador<br/>(contador o socio)<br/>Ve o registra en el negocio"]
    A["👤 Administrador FinMicro<br/>Gestiona planes y usuarios"]
    F["FinMicro<br/>Plataforma web de gestión<br/>financiera para microempresas"]
    M["mindicador.cl<br/>UF, UTM, dólar, IPC<br/>(datos del Banco Central)"]
    P["Khipu / Flow.cl<br/>Pasarelas de pago"]
    E["Servicio de correo<br/>(Amazon SES)"]

    U -- HTTPS --> F
    C -- HTTPS --> F
    A -- HTTPS /admin --> F
    F -- "HTTPS, JSON (caché 6 h)" --> M
    F -- "Crea pagos / recibe webhooks" --> P
    F -- SMTP --> E
    E -. "Recuperación de clave,<br/>invitaciones" .-> U
```

## Nivel 2 — Contenedores

```mermaid
flowchart TB
    subgraph EC2["Instancia EC2 · Ubuntu 24.04 · ufw + fail2ban"]
        N["Nginx<br/>Proxy inverso, HTTPS (Let's Encrypt)<br/>puertos 80/443"]
        subgraph D["Contenedor Docker"]
            G["Gunicorn + Django 6<br/>Aplicación web (3 workers)<br/>127.0.0.1:8000"]
            W["WhiteNoise<br/>Archivos estáticos"]
        end
        V[("Volumen Docker<br/>SQLite<br/>/app/data")]
    end
    B["Navegador<br/>HTML + CSS + Chart.js"]
    S3[("Amazon S3<br/>Respaldos diarios<br/>(actividad 6.2)")]

    B -- HTTPS --> N
    N -- "HTTP local" --> G
    G --- W
    G -- "lectura/escritura" --> V
    V -. "copia diaria" .-> S3
```

## Nivel 3 — Componentes de la aplicación Django

```mermaid
flowchart TB
    subgraph Django["Aplicación Django (finmicroaw)"]
        MW["NegocioActivoMiddleware<br/>request.negocio / rol"]
        ACC["accounts<br/>Usuario, RUT, configuración,<br/>colaboradores, datos personales"]
        FIN["finances<br/>Categorías, movimientos,<br/>panel"]
        TAX["taxes<br/>IVA, honorarios"]
        PRO["projections<br/>Proyección, VAN/TIR"]
        SUB["subscriptions<br/>Planes, suscripciones,<br/>pasarelas (adaptadores)"]
        CORE["core<br/>Portada, indicadores<br/>(BancoCentralService)"]
    end
    MW --> FIN & TAX & PRO
    ACC --> SUB
    FIN --> ACC
    PRO --> FIN
    TAX -. "Sprint 4: IVA automático" .-> FIN
    CORE --> EXT1["mindicador.cl"]
    SUB --> EXT2["Khipu / Flow"]
```

**Decisiones de diseño**

| Decisión | Motivo |
|---|---|
| Una app Django por dominio | Límites claros; cada app tiene sus modelos, vistas, servicios y pruebas. |
| Cálculos en `services.py`, sin dependencias de Django | Se prueban con `SimpleTestCase`, sin base de datos (rápido, aislado). |
| Aislación por `request.negocio` | Multi-tenant lógico: toda consulta filtra por el negocio activo (RNF-03). |
| Patrón adaptador para pagos e indicadores | Cambiar Khipu/Flow o pasar a la API oficial del Banco Central no toca las vistas. |
| SQLite en el MVP | Cero administración y respaldo como archivo. Ver límites y migración en el plan de escalamiento. |

## Stack tecnológico (actividad 3.5)

| Capa | Tecnología | Versión | Por qué |
|---|---|---|---|
| Lenguaje | Python | 3.13 (Docker) | El equipo lo domina; ecosistema financiero y de IA. |
| Framework | Django | 6.0 | Autenticación, admin, ORM, migraciones, protección CSRF/XSS incluidas. |
| Servidor de aplicación | Gunicorn | 23 | Estándar para Django en producción. |
| Estáticos | WhiteNoise | 6.9 | Sirve CSS sin configurar Nginx para ello. |
| Base de datos | SQLite → PostgreSQL | — | Ver plan de escalamiento. |
| Frontend | Plantillas Django + CSS propio + Chart.js 4 | — | Sin build de JavaScript; liviano en celulares de gama baja. |
| Contenedores | Docker + Docker Compose | — | Mismo entorno en desarrollo, CI y producción. |
| Proxy / TLS | Nginx + Let's Encrypt (certbot) | — | HTTPS gratuito y renovación automática. |
| Infraestructura | AWS EC2 (t3.micro o t3.small), S3, SES, Budgets | — | Plan gratuito inicial; ver actividad 6.0. |
| CI | GitHub Actions | — | Integrado al repositorio. |
| Indicadores | mindicador.cl | — | Gratis y sin credenciales; misma fuente que el Banco Central. |
| Pagos | Khipu, Flow.cl | — | Pasarelas locales (informe, PESTEL). |
