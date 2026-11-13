"""
X-11 · Prueba de carga (RNF-07: p95 < 800 ms con 50 usuarios concurrentes).

Cada usuario virtual inicia sesión con una cuenta de prueba y recorre las
pantallas principales, registrando de vez en cuando un movimiento.
Ejecutar contra un ambiente de pruebas, nunca contra producción con datos
reales:

    python manage.py crear_usuarios_prueba --password "ClaveDeCarga.2026"
    locust -f deploy/carga/locustfile.py --host http://localhost:8000 \\
        --headless -u 50 -r 10 -t 2m --csv resultados

Variables: FINMICRO_USUARIO (por omisión prueba_premium, sin límite de
movimientos) y FINMICRO_CLAVE.
"""
import os
import re
from datetime import date

from locust import HttpUser, between, task

USUARIO = os.environ.get("FINMICRO_USUARIO", "prueba_premium")
CLAVE = os.environ.get("FINMICRO_CLAVE", "ClaveDeCarga.2026")
CSRF = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')
TRANSPORTE = re.compile(r'<option value="(\d+)"[^>]*>Transporte \(Gasto\)')


class Microempresario(HttpUser):
    wait_time = between(1, 3)

    def _token(self, url):
        respuesta = self.client.get(url, name=url)
        encontrado = CSRF.search(respuesta.text)
        return encontrado.group(1) if encontrado else ""

    def on_start(self):
        token = self._token("/cuenta/login/")
        self.client.post("/cuenta/login/", {"username": USUARIO, "password": CLAVE, "csrfmiddlewaretoken": token},
                         name="/cuenta/login/ [POST]")
        respuesta = self.client.get("/finanzas/", name="/finanzas/")
        if "/terminos/aceptar/" in respuesta.url:   # RF-29: primera vez de la cuenta de prueba
            token = CSRF.search(respuesta.text).group(1)
            self.client.post("/cuenta/terminos/aceptar/", {"acepta": "on", "csrfmiddlewaretoken": token},
                             name="/cuenta/terminos/aceptar/ [POST]")

    @task(5)
    def panel(self):
        self.client.get("/finanzas/", name="/finanzas/")

    @task(3)
    def movimientos(self):
        self.client.get("/finanzas/movimientos/", name="/finanzas/movimientos/")

    @task(2)
    def buscar(self):
        self.client.get("/finanzas/movimientos/?q=venta", name="/finanzas/movimientos/?q=")

    @task(2)
    def indicadores(self):
        self.client.get("/finanzas/indicadores/", name="/finanzas/indicadores/")

    @task(1)
    def impuestos(self):
        self.client.get("/impuestos/", name="/impuestos/")

    @task(1)
    def proyeccion(self):
        self.client.get("/proyecciones/ingresos/", name="/proyecciones/ingresos/")

    @task(1)
    def registrar_gasto(self):
        formulario = self.client.get("/finanzas/movimientos/nuevo/", name="/finanzas/movimientos/nuevo/").text
        token, categoria = CSRF.search(formulario), TRANSPORTE.search(formulario)
        if not token or not categoria:
            return
        self.client.post("/finanzas/movimientos/nuevo/", {
            "csrfmiddlewaretoken": token.group(1), "tipo": "gasto", "categoria": categoria.group(1), "monto": "1500",
            "fecha": date.today().isoformat(), "descripcion": "Prueba de carga",
        }, name="/finanzas/movimientos/nuevo/ [POST]")
