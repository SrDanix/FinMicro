# Infraestructura: cuenta AWS, ambientes, CI y endurecimiento

**Actividades 6.0, 6.1 y 6.4** · Responsables: Danilo (6.0, 6.1), Marcelo (6.4)

## 6.0 Verificación de la cuenta AWS y presupuesto de alertas

> ⚠️ **Requiere una persona con acceso a la cuenta de AWS.** Esto no se puede hacer
> desde el repositorio; aquí queda el procedimiento y los archivos listos.

**1. Verificar el régimen de la cuenta.** Desde julio de 2025, las cuentas nuevas de AWS
eligen entre un *plan gratuito* (créditos por un período limitado; al vencer, la cuenta
se cierra si no se pasa a pago) y un *plan pagado*. Las cuentas anteriores mantienen el
esquema antiguo de capa gratuita de 12 meses. En la consola: **Billing and Cost
Management → Free Tier** (o *Plan de la cuenta*). Anotar en el informe:

- [ ] Tipo de plan de la cuenta y fecha de vencimiento de los créditos o de la capa gratuita
- [ ] Créditos disponibles
- [ ] Región elegida (recomendada: `sa-east-1`, São Paulo, la más cercana a Chile; verificar que la instancia elegida esté cubierta por el plan)

**2. Crear el presupuesto con alertas** (USD 15/mes; avisos al 50 % y 80 % real y 100 % proyectado, RNF-16).
Editar el correo en [deploy/aws/alertas.json](../deploy/aws/alertas.json) y ejecutar con AWS CLI:

```bash
aws budgets create-budget --account-id TU_ID_DE_CUENTA --budget file://deploy/aws/presupuesto.json --notifications-with-subscribers file://deploy/aws/alertas.json
```

O desde la consola: **Billing → Budgets → Create budget → Cost budget**, con los mismos valores.

**3. Seguridad mínima de la cuenta:** MFA en el usuario raíz, no usar el usuario raíz
para el día a día (crear un usuario IAM o usar IAM Identity Center), y no generar llaves
de acceso para el raíz.

## 6.1 Ambientes e integración continua

| Ambiente | Dónde | Cómo se levanta | Base de datos | Correo |
|---|---|---|---|---|
| **Desarrollo** | PC de cada integrante | `python manage.py runserver` (SQLite) o `docker compose up --build` (PostgreSQL) | SQLite o PostgreSQL local | Consola |
| **Integración (CI)** | GitHub Actions | Automático en cada push y PR a `main` | SQLite **y** PostgreSQL 17 efímeras | En memoria |
| **Producción** | EC2 + Nginx + HTTPS | `docker compose -f docker-compose.prod.yml up -d --build` | Amazon RDS PostgreSQL ([doc 17](17_base_de_datos_aws.md)) o SQLite en volumen (E0) | SMTP (SES) |

**CI** ([.github/workflows/ci.yml](../.github/workflows/ci.yml)): instala dependencias,
verifica que no falten migraciones, corre las pruebas, ejecuta el checklist de
despliegue de Django (`check --deploy`) y construye la imagen Docker. Un PR no se integra
si la CI falla ([CONTRIBUTING.md](../CONTRIBUTING.md) explica cómo exigirlo en GitHub).

### Despliegue en la instancia (cuando exista)

```bash
# En la instancia, una sola vez
sudo apt-get install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx git
git clone https://github.com/SrDanix/FinMicro.git && cd FinMicro
cp .env.example .env            # completar SECRET_KEY, ALLOWED_HOSTS, dominio, correo
sudo bash deploy/endurecer_servidor.sh
sudo cp deploy/nginx/finmicro.conf /etc/nginx/sites-available/finmicro   # editar TU_DOMINIO
sudo ln -s /etc/nginx/sites-available/finmicro /etc/nginx/sites-enabled/
sudo certbot --nginx -d TU_DOMINIO
docker compose -f docker-compose.prod.yml up -d --build

# Cada actualización
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

## 6.4 Endurecimiento del servidor y firewall

Con una sola instancia EC2, el firewall y el endurecimiento son responsabilidad del
equipo, no del proveedor. Dos capas:

**Security Group de AWS** (se configura en la consola al crear la instancia):

| Puerto | Origen | Uso |
|---|---|---|
| 22 (SSH) | **Solo las IP del equipo** | Administración |
| 80 (HTTP) | 0.0.0.0/0 | Redirección a HTTPS y validación de certbot |
| 443 (HTTPS) | 0.0.0.0/0 | Aplicación |

Todo lo demás cerrado. El puerto 8000 del contenedor **no** se abre: Docker lo publica
solo en `127.0.0.1` ([docker-compose.prod.yml](../docker-compose.prod.yml)).

**Sistema operativo:** [deploy/endurecer_servidor.sh](../deploy/endurecer_servidor.sh)
aplica actualizaciones automáticas de seguridad, SSH solo con llave y sin root, firewall
`ufw` (22, 80, 443), `fail2ban` contra fuerza bruta y ajustes de red del kernel. Aborta
si no encuentra una llave SSH cargada, para no dejar al equipo sin acceso.

**Aplicación:** con `DJANGO_DEBUG=False` se activan redirección a HTTPS, cookies seguras
y HSTS de 7 días; la CI verifica con `check --deploy` que no falte ninguna opción.
