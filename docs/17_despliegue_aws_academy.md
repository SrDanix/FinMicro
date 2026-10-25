# Despliegue en AWS Academy (Learner Lab), paso a paso

Guía para levantar FinMicro en una instancia EC2 del **Learner Lab de AWS Academy** y
verlo en el navegador. Complementa [11_infraestructura.md](11_infraestructura.md), que
describe el despliegue en una cuenta AWS normal.

```
Navegador ──► Internet ──► [Security Group de AWS] ──► Instancia EC2 (Ubuntu 24.04)
                                                         ├─ Nginx (puertos 80/443)   ← recibe a los visitantes
                                                         └─ Docker: FinMicro en 127.0.0.1:8000 (solo interno)
                                                               └─ SQLite en el volumen finmicro_datos
```

Se hace en dos etapas:

1. **Etapa 1:** FinMicro funcionando en `http://TU_IP`.
2. **Etapa 2 (recomendada):** HTTPS con un dominio gratuito de DuckDNS.

## Diferencias del Learner Lab frente a una cuenta normal

| Tema | En el Learner Lab |
|---|---|
| Región | Solo `us-east-1` (N. Virginia) o `us-west-2`. **No** `sa-east-1` |
| Facturación, presupuestos, IAM | Sin acceso. El lab controla el crédito (USD 50). Se omite la parte 6.0 de la doc 11 |
| Sesión | Dura ~4 h. Al terminar, la instancia se **detiene** y vuelve con *Start Lab* |
| Fin del curso | AWS Academy **borra todo**. Respaldar antes |
| Llave SSH | Usar la llave `vockey` que trae el lab (*AWS Details → Download PEM* = `labsuser.pem`) |
| Dominios | No se pueden registrar en Route 53. Usar DuckDNS o solo la IP |
| Correo (SES) | Queda en sandbox. Para el curso, los correos se ven en los logs |
| Tipos de instancia | Solo pequeños: usar `t3.small` o `t3.micro` |

---

# ETAPA 1 — FinMicro funcionando por IP

Los pasos 0 a 5 se hacen en la **consola web de AWS**. Desde el paso 6 todo se escribe
en la **terminal del servidor** (EC2 Instance Connect, pantalla negra en el navegador).

## Paso 0 — Iniciar el laboratorio (consola)
1. AWS Academy → curso → **Modules → Learner Lab**.
2. **Start Lab** y esperar que el círculo junto a "AWS" se ponga **verde**.
3. Clic en **AWS** para abrir la consola.

**Por qué:** la consola solo funciona con la sesión activa.

## Paso 1 — Región (consola)
Arriba a la derecha debe decir **N. Virginia (us-east-1)**. Todo lo que sigue va en la
misma región.

## Paso 2 — Instancia EC2 (consola)
**EC2 → Instances → Launch instance** (o revisar la existente `finmicro-prod`):

| Ajuste | Valor | Por qué |
|---|---|---|
| Nombre | `finmicro-prod` | Identificarla |
| AMI | **Ubuntu Server 24.04 LTS** | Es para la que está escrito `deploy/endurecer_servidor.sh` |
| Tipo | **t3.small** (o t3.micro) | 2 GB de RAM van holgados; con t3.micro hay que agregar swap (paso 9.5) |
| Key pair | **vockey** | El script de endurecimiento exige una llave cargada para no dejarte fuera |
| Almacenamiento | **20 GB gp3** | Docker e imágenes llenan los 8 GB por defecto |
| Auto-assign public IP | **Enable** | Para entrar desde internet |

## Paso 3 — IP fija / Elastic IP (consola)
1. **EC2 → Network & Security → Elastic IPs → Allocate Elastic IP address → Allocate**.
2. Seleccionarla → **Actions → Associate Elastic IP address** → Instance `finmicro-prod` → **Associate**.
3. Anotar la IP. En esta guía es `TU_IP`.

**Por qué:** sin ella la IP cambia cada vez que el lab enciende la instancia.

## Paso 4 — Security Group (consola)
**EC2 → Instances → `finmicro-prod` → pestaña Security** → clic en el Security Group →
**Edit inbound rules**. Debe quedar así, **sin reglas repetidas**:

```
SSH    22   18.206.107.24/29   ← EC2 Instance Connect de us-east-1 (o 0.0.0.0/0)
SSH    22   Mi IP              ← opcional, para conectarse desde el PC con labsuser.pem
HTTP   80   0.0.0.0/0          ← visitantes
HTTPS  443  0.0.0.0/0          ← visitantes (etapa 2)
```

- La terminal del navegador entra desde servidores de AWS, no desde tu IP. Por eso
  "Mi IP" sola no basta para EC2 Instance Connect. Si la prefix list
  `com.amazonaws.us-east-1.ec2-instance-connect` no aparece (pasa en el lab), usar
  `18.206.107.24/29` en *Custom*. Si aun así no conecta, `0.0.0.0/0` es aceptable en el
  lab porque tras el paso 9 solo se entra con llave y `fail2ban` bloquea intentos.
- Error *"the specified rule ... already exists"*: hay dos filas idénticas. **Back**,
  borrar o cambiar una de ellas, **Save rules**.
- El puerto 8000 **no** se abre: solo Nginx lo usa desde dentro.

## Paso 5 — Abrir la terminal del servidor (consola)
1. **EC2 → Instances** → marcar `finmicro-prod` → **Connect**.
2. Pestaña **EC2 Instance Connect**, usuario `ubuntu` → **Connect**.
3. Se abre una pestaña negra con `ubuntu@ip-172-31-xx-xx:~$`. Ya estás en el servidor.

Pegar: **Ctrl+Shift+V** o clic derecho → Pegar. Copiar: **Ctrl+Shift+C**.

Alternativa: *AWS Details → Download PEM* y desde el PC `ssh -i labsuser.pem ubuntu@TU_IP`.

## Paso 6 — Instalar el software (terminal)
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 nginx git
sudo usermod -aG docker ubuntu
exit
```
Volver a conectarse (paso 5) y comprobar:
```bash
docker --version
docker compose version
```
**Por qué:** Docker ejecuta FinMicro igual que en el PC y en la CI; Nginx da la cara a
internet; git baja el código. El `exit` es necesario para que el permiso de Docker se aplique.

## Paso 7 — Bajar el proyecto (terminal)
```bash
git clone https://github.com/SrDanix/FinMicro.git
cd FinMicro
```
Si el repo es privado, como contraseña se usa un *token* de GitHub (Settings → Developer
settings → Personal access tokens → Fine-grained, *Contents: Read-only*).

## Paso 8 — Archivo `.env` (terminal)
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # copiar la clave
cp .env.example .env
nano .env
```
Cambiar (con tu IP real):
```ini
DJANGO_SECRET_KEY=la-clave-que-generaste
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=TU_IP
DJANGO_HTTPS=False
DJANGO_CSRF_TRUSTED_ORIGINS=http://TU_IP
PAGOS_MODO_SIMULADO=True
```
nano: flechas para moverse, **Ctrl+O** + Enter guarda, **Ctrl+X** sale. Revisar con `cat .env`.

| Variable | Por qué |
|---|---|
| `DJANGO_SECRET_KEY` | Firma sesiones y cookies. Única y nunca en GitHub |
| `DJANGO_DEBUG=False` | Con `True` los errores muestran código interno a cualquiera |
| `DJANGO_ALLOWED_HOSTS` | Si falta la IP o dominio → **Bad Request (400)** |
| `DJANGO_HTTPS=False` | Aún no hay certificado; con `True` redirige a `https://` y no abre |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Si falta → **Forbidden (403) CSRF** al iniciar sesión |
| `PAGOS_MODO_SIMULADO=True` | Sin credenciales reales de Khipu/Flow |

## Paso 9 — Endurecer el servidor (terminal)
```bash
cd ~/FinMicro
sudo bash deploy/endurecer_servidor.sh
```
Si aparece una pantalla morada preguntando qué servicios reiniciar: **Enter**.

**Por qué:** actualizaciones de seguridad automáticas, SSH solo con llave, firewall `ufw`
(22, 80, 443), `fail2ban` y ajustes de red. No depende de Docker.

## Paso 9.5 — Dejar Docker listo (terminal)
```bash
# Arrancar solo al encender la instancia (el lab la apaga y enciende)
sudo systemctl enable --now docker
systemctl is-enabled docker            # → enabled

# Limitar los logs para que no llenen el disco
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
EOF
sudo systemctl restart docker

# Usar Docker sin sudo
docker ps                              # tabla vacía = bien; "permission denied" = exit y reconectar
```
Solo con **t3.micro** (1 GB de RAM), agregar 2 GB de swap para que el `--build` no falle:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Paso 10 — Nginx (terminal)
```bash
sudo cp deploy/nginx/finmicro.conf /etc/nginx/sites-available/finmicro
sudo sed -i 's/TU_DOMINIO/TU_IP/' /etc/nginx/sites-available/finmicro   # tu IP real
sudo ln -s /etc/nginx/sites-available/finmicro /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```
**Por qué:** Nginx recibe las visitas en el puerto 80 y las pasa a la app en
`127.0.0.1:8000`. Se quita `default` porque es la página de bienvenida de Nginx.

## Paso 11 — Levantar FinMicro (terminal)
```bash
cd ~/FinMicro
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```
Al arrancar, el contenedor aplica las migraciones y levanta Gunicorn. Los datos quedan en
el volumen `finmicro_datos` y `restart: unless-stopped` lo vuelve a levantar solo.

### Comprobar, de adentro hacia afuera
```bash
docker compose -f docker-compose.prod.yml ps                  # a) "web" en Up/running
curl -I -H "Host: TU_IP" http://127.0.0.1:8000                # b) 200 o 302
curl -I http://TU_IP                                          # c) 200 o 302
```
- Falla **a** → `docker compose -f docker-compose.prod.yml logs --tail 50 web` (suele ser el `.env`).
- **b** da 400 → falta la IP en `DJANGO_ALLOWED_HOSTS`.
- **b** bien y **c** mal → Nginx (paso 10) o puerto 80 del Security Group (paso 4).

Abrir **`http://TU_IP`** en el navegador. ✅

---

# ETAPA 2 — HTTPS con DuckDNS (recomendado)

Let's Encrypt solo da certificados a dominios, no a IPs, y el lab no permite comprar
dominios. DuckDNS da subdominios gratis.

## Paso 12 — Dominio en DuckDNS (navegador)
1. https://www.duckdns.org → iniciar sesión con GitHub o Google.
2. Crear un subdominio, p. ej. `finmicro` → `finmicro.duckdns.org`.
3. En **current ip** poner la Elastic IP → **update ip**.

## Paso 13 — Certificado (terminal)
```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo sed -i 's/server_name .*/server_name finmicro.duckdns.org;/' /etc/nginx/sites-available/finmicro
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d finmicro.duckdns.org
```
Certbot configura el 443, redirige http → https y deja la renovación automática.

## Paso 14 — Django en modo HTTPS (terminal)
`nano ~/FinMicro/.env`:
```ini
DJANGO_ALLOWED_HOSTS=finmicro.duckdns.org,TU_IP
DJANGO_HTTPS=True
DJANGO_CSRF_TRUSTED_ORIGINS=https://finmicro.duckdns.org
```
```bash
cd ~/FinMicro
docker compose -f docker-compose.prod.yml up -d --force-recreate
```
Abrir **https://finmicro.duckdns.org** 🔒. Ojo: activa HSTS por 7 días; no volver a
`http` con ese dominio.

---

# Uso diario

| Situación | Qué hacer |
|---|---|
| Poner la página en línea | *Start Lab*; en 1-2 min arrancan instancia, Nginx y FinMicro |
| Publicar cambios | `cd ~/FinMicro && git pull && docker compose -f docker-compose.prod.yml up -d --build` |
| Respaldar | **EC2 → Elastic Block Store → Volumes** → disco de la instancia → **Actions → Create snapshot**. Antes de cambios grandes y **antes de que termine el curso** |
| Ver errores / correos | `docker compose -f docker-compose.prod.yml logs --tail 100 web` |

# Problemas típicos

| Síntoma | Causa probable | Solución |
|---|---|---|
| La página no carga (tiempo agotado) | Lab detenido o faltan 80/443 en el Security Group | *Start Lab*; paso 4 |
| **Bad Request (400)** | IP/dominio no está en `DJANGO_ALLOWED_HOSTS` | Corregir `.env` + `up -d --force-recreate` |
| **Forbidden (403) CSRF** | `DJANGO_CSRF_TRUSTED_ORIGINS` mal (`http` vs `https`) | Igual que arriba |
| **502 Bad Gateway** | La app no está corriendo | `ps` y `logs` del paso 11 |
| Redirige a `https://` y falla | `DJANGO_HTTPS=True` sin certificado | Volver a `False` o hacer la etapa 2 |
| EC2 Instance Connect no conecta | Falta la regla SSH de `us-east-1` | Paso 4 |
| *"rule ... already exists"* | Regla duplicada en el Security Group | Paso 4 |
