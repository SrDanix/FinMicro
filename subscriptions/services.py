"""
Lógica de negocio de suscripciones: alta del Plan Básico por defecto y
adaptadores de pasarela de pago (Khipu / Flow.cl — Sección 3.2 PESTEL del
informe: "Pasarelas de pago locales (Khipu, Flow.cl)").

Diseño: ambas pasarelas implementan la misma interfaz `PasarelaPago`
(iniciar_pago / confirmar_pago), así que las vistas nunca llaman a Khipu o
Flow directamente — llaman a `obtener_pasarela(nombre)`. Esto permite
agregar una tercera pasarela sin tocar views.py.

MODO SIMULADO: si no hay credenciales configuradas en el archivo .env
(API keys reales de Khipu/Flow), las pasarelas no llaman a la red: generan
una URL de pago falsa que apunta a una vista interna de confirmación, para
que todo el flujo de "suscribirse a Premium" se pueda probar de punta a
punta sin tener una cuenta de comercio real todavía. Cuando tengas las
credenciales, basta con completarlas en .env — el código no cambia.
"""
import hashlib
import hmac
import uuid
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.urls import reverse

from .models import Plan, Suscripcion


def asegurar_plan_basico(usuario):
    """Crea (si no existe) el Plan Básico y suscribe al usuario a él.

    Se usa al registrarse (accounts.views.registro) para que ningún
    usuario quede sin plan asignado.
    """
    plan_basico, _ = Plan.objects.get_or_create(
        codigo=Plan.Codigo.BASICO,
        defaults={
            "nombre": "Plan Básico",
            "precio_mensual_clp": 0,
            "con_publicidad": True,
            "limite_movimientos_mensuales": 60,
            "incluye_proyecciones": True,
            "incluye_evaluador_viabilidad": False,
            "descripcion": "Gratis, financiado con publicidad. Gestión financiera e "
            "impuestos incluidos, con tope de 60 movimientos al mes.",
        },
    )
    if not usuario.suscripcion_activa:
        Suscripcion.objects.create(
            usuario=usuario,
            plan=plan_basico,
            estado=Suscripcion.Estado.ACTIVA,
            metodo_pago=Suscripcion.MetodoPago.NINGUNO,
        )
    return plan_basico


def asegurar_plan_premium():
    plan_premium, _ = Plan.objects.get_or_create(
        codigo=Plan.Codigo.PREMIUM,
        defaults={
            "nombre": "Plan Premium",
            "precio_mensual_clp": 9990,
            "con_publicidad": False,
            "limite_movimientos_mensuales": None,
            "incluye_proyecciones": True,
            "incluye_evaluador_viabilidad": True,
            "descripcion": "Sin publicidad, movimientos ilimitados y evaluador de "
            "viabilidad (VAN/TIR/Payback) para tu propio negocio.",
        },
    )
    return plan_premium


class PasarelaPago:
    """Interfaz común. Cada pasarela concreta implementa estos dos métodos."""

    nombre = "base"

    def iniciar_pago(self, request, suscripcion: Suscripcion) -> str:
        """Debe devolver la URL a la que se redirige al usuario para pagar."""
        raise NotImplementedError

    def confirmar_pago(self, datos_notificacion: dict) -> bool:
        """Procesa el webhook/notificación de la pasarela.

        Devuelve True si el pago fue aprobado. La vista que recibe el
        webhook es responsable de buscar la Suscripcion por
        `referencia_pago` y llamar a `.activar()`.
        """
        raise NotImplementedError

    def _modo_simulado(self) -> bool:
        return getattr(settings, "PAGOS_MODO_SIMULADO", True)


class KhipuGateway(PasarelaPago):
    """Adaptador para Khipu API v3 (Pagos Instantáneos).

    Documentación oficial: https://docs.khipu.com/apis/v3/instant-payments
    Endpoint: POST https://payment-api.khipu.com/v3/payments
    Autenticación: header 'x-api-key'.
    IMPORTANTE: antes de usar en producción, verifica el contrato exacto
    (nombres de campos, códigos de estado) contra la documentación vigente
    de Khipu — las APIs de pago cambian y este adaptador es un punto de
    partida funcional, no una copia certificada del contrato actual.
    """

    nombre = "khipu"
    API_URL = "https://payment-api.khipu.com/v3/payments"

    def iniciar_pago(self, request, suscripcion: Suscripcion) -> str:
        api_key = getattr(settings, "KHIPU_API_KEY", "")
        transaction_id = f"finmicro-{suscripcion.id}-{uuid.uuid4().hex[:8]}"

        if self._modo_simulado() or not api_key:
            suscripcion.referencia_pago = transaction_id
            suscripcion.metodo_pago = Suscripcion.MetodoPago.KHIPU
            suscripcion.save(update_fields=["referencia_pago", "metodo_pago"])
            return request.build_absolute_uri(
                reverse("subscriptions:pago_simulado", args=[suscripcion.id])
            )

        payload = {
            "subject": f"FinMicro — {suscripcion.plan.nombre}",
            "amount": suscripcion.plan.precio_mensual_clp,
            "currency": "CLP",
            "transaction_id": transaction_id,
            "return_url": request.build_absolute_uri(reverse("subscriptions:mi_suscripcion")),
            "cancel_url": request.build_absolute_uri(reverse("subscriptions:planes")),
            "notify_url": request.build_absolute_uri(reverse("subscriptions:webhook_khipu")),
        }
        respuesta = requests.post(
            self.API_URL,
            json=payload,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            timeout=10,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()

        suscripcion.referencia_pago = datos["payment_id"]
        suscripcion.metodo_pago = Suscripcion.MetodoPago.KHIPU
        suscripcion.save(update_fields=["referencia_pago", "metodo_pago"])
        return datos["payment_url"]

    def confirmar_pago(self, datos_notificacion: dict) -> bool:
        # Khipu notifica el estado del pago en el cuerpo del webhook.
        return datos_notificacion.get("status") == "done"


class FlowGateway(PasarelaPago):
    """Adaptador para Flow.cl (payment/create).

    Documentación oficial: https://www.flow.cl/docs/api.html
    Flow exige firmar cada request: se ordenan los parámetros
    alfabéticamente por nombre de campo, se concatena "clave"+"valor" de
    cada uno, y se firma el resultado con HMAC-SHA256 usando el
    secretKey del comercio. La firma va en el parámetro "s".
    IMPORTANTE: mismo aviso que en KhipuGateway — verificar contra la
    documentación vigente antes de producción.
    """

    nombre = "flow"

    def _api_url(self) -> str:
        return getattr(settings, "FLOW_API_URL", "https://sandbox.flow.cl/api")

    def _firmar(self, params: dict, secret_key: str) -> str:
        params_ordenados = sorted(params.items())
        cadena = "".join(f"{clave}{valor}" for clave, valor in params_ordenados)
        return hmac.new(secret_key.encode(), cadena.encode(), hashlib.sha256).hexdigest()

    def iniciar_pago(self, request, suscripcion: Suscripcion) -> str:
        api_key = getattr(settings, "FLOW_API_KEY", "")
        secret_key = getattr(settings, "FLOW_SECRET_KEY", "")
        commerce_order = f"finmicro-{suscripcion.id}-{uuid.uuid4().hex[:8]}"

        if self._modo_simulado() or not api_key or not secret_key:
            suscripcion.referencia_pago = commerce_order
            suscripcion.metodo_pago = Suscripcion.MetodoPago.FLOW
            suscripcion.save(update_fields=["referencia_pago", "metodo_pago"])
            return request.build_absolute_uri(
                reverse("subscriptions:pago_simulado", args=[suscripcion.id])
            )

        params = {
            "apiKey": api_key,
            "commerceOrder": commerce_order,
            "subject": f"FinMicro — {suscripcion.plan.nombre}",
            "currency": "CLP",
            "amount": suscripcion.plan.precio_mensual_clp,
            "email": suscripcion.usuario.email,
            "urlConfirmation": request.build_absolute_uri(
                reverse("subscriptions:webhook_flow")
            ),
            "urlReturn": request.build_absolute_uri(reverse("subscriptions:mi_suscripcion")),
        }
        params["s"] = self._firmar(params, secret_key)

        respuesta = requests.post(
            f"{self._api_url()}/payment/create",
            data=urlencode(params),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()

        suscripcion.referencia_pago = datos["token"]
        suscripcion.metodo_pago = Suscripcion.MetodoPago.FLOW
        suscripcion.save(update_fields=["referencia_pago", "metodo_pago"])
        return f"{datos['url']}?token={datos['token']}"

    def confirmar_pago(self, datos_notificacion: dict) -> bool:
        # Flow entrega un "token"; el estado real se consulta aparte con
        # payment/getStatus. Aquí se asume que la vista del webhook ya
        # hizo esa consulta y pasa el resultado como "status" == 2 (pagada).
        return datos_notificacion.get("status") == 2


def obtener_pasarela(nombre: str) -> PasarelaPago:
    pasarelas = {"khipu": KhipuGateway, "flow": FlowGateway}
    clase = pasarelas.get(nombre)
    if not clase:
        raise ValueError(f"Pasarela de pago desconocida: {nombre}")
    return clase()