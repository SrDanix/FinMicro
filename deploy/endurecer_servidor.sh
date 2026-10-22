#!/usr/bin/env bash
# =====================================================================
# Endurecimiento de la instancia EC2 de FinMicro (actividad 6.4).
# Probado para Ubuntu Server 24.04 LTS. Ejecutar UNA vez, como root:
#     sudo bash endurecer_servidor.sh
#
# ANTES de ejecutarlo: confirma que entras por SSH con llave (no con
# contraseña). El script desactiva el acceso por contraseña y el login
# directo de root; si no tienes una llave cargada, quedarás fuera.
# =====================================================================
set -euo pipefail

if [[ $EUID -ne 0 ]]; then echo "Ejecuta con sudo." >&2; exit 1; fi
if [[ ! -s "/home/${SUDO_USER:-ubuntu}/.ssh/authorized_keys" ]]; then
  echo "No hay llave SSH en ~/.ssh/authorized_keys: abortando para no dejarte fuera." >&2
  exit 1
fi

echo "==> 1. Actualizaciones del sistema y actualizaciones de seguridad automáticas"
apt-get update -y
apt-get upgrade -y
apt-get install -y unattended-upgrades fail2ban ufw
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> 2. SSH: solo con llave, sin root"
install -d /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/90-finmicro.conf <<'CONF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
CONF
sshd -t && systemctl reload ssh

echo "==> 3. Firewall del sistema operativo (además del Security Group de AWS)"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> 4. fail2ban: bloquea IPs con intentos fallidos de SSH"
cat > /etc/fail2ban/jail.d/finmicro.local <<'CONF'
[sshd]
enabled = true
maxretry = 5
findtime = 10m
bantime = 1h
CONF
systemctl enable --now fail2ban
systemctl restart fail2ban

echo "==> 5. Ajustes de red del kernel"
cat > /etc/sysctl.d/90-finmicro.conf <<'CONF'
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.tcp_syncookies = 1
CONF
sysctl --system >/dev/null

echo "==> Listo. Estado del firewall:"
ufw status verbose
