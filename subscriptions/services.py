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
import logging
import uuid
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import Plan, Suscripcion

logger = logging.getLogger(__name__)

# RF-28: Premium se paga por mes. Al vencer hay unos días de gracia antes
# de volver al Plan Básico, y se avisa unos días antes del vencimiento.
DURACION_PERIODO = relativedelta(months=1)
DIAS_AVISO_VENCIMIENTO = 3
DIAS_GRACIA = 3


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


@dataclass(frozen=True)
class EstadoPago:
    """Estado de un pago según la propia pasarela (nunca según el aviso entrante)."""

    pagado: bool
    monto: int
    orden: str


class ErrorPasarela(RuntimeError):
    pass


class PasarelaPago:
    """Interfaz común: iniciar_pago y consultar_estado."""

    nombre = "base"

    def iniciar_pago(self, request, suscripcion: Suscripcion) -> str:
        """Debe devolver la URL a la que se redirige al usuario para pagar."""
        raise NotImplementedError

    def consultar_estado(self, referencia: str) -> EstadoPago:
        """Pregunta a la pasarela, con nuestras credenciales, el estado real del pago.

        RF-27: un aviso (webhook) puede venir de cualquiera; solo la respuesta
        de la pasarela autoriza a activar un plan.
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

    def consultar_estado(self, referencia: str) -> EstadoPago:
        api_key = getattr(settings, "KHIPU_API_KEY", "")
        if self._modo_simulado() or not api_key:
            raise ErrorPasarela("Khipu no está configurado (modo simulado).")
        try:
            respuesta = requests.get(f"{self.API_URL}/{referencia}", headers={"x-api-key": api_key}, timeout=10)
            respuesta.raise_for_status()
            datos = respuesta.json()
            return EstadoPago(datos.get("status") == "done", int(float(datos["amount"])), str(datos["transaction_id"]))
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            raise ErrorPasarela(f"No se pudo consultar el pago en Khipu: {error}") from error


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
            # Flow devuelve al usuario con un POST: va a una vista sin CSRF que solo redirige.
            "urlReturn": request.build_absolute_uri(reverse("subscriptions:retorno_pago")),
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

    def consultar_estado(self, referencia: str) -> EstadoPago:
        """payment/getStatus firmado. Estados de Flow: 1 pendiente, 2 pagada, 3 rechazada, 4 anulada."""
        api_key = getattr(settings, "FLOW_API_KEY", "")
        secret_key = getattr(settings, "FLOW_SECRET_KEY", "")
        if self._modo_simulado() or not api_key or not secret_key:
            raise ErrorPasarela("Flow no está configurado (modo simulado).")
        params = {"apiKey": api_key, "token": referencia}
        params["s"] = self._firmar(params, secret_key)
        try:
            respuesta = requests.get(f"{self._api_url()}/payment/getStatus", params=params, timeout=10)
            respuesta.raise_for_status()
            datos = respuesta.json()
            return EstadoPago(int(datos["status"]) == 2, int(float(datos["amount"])), str(datos["commerceOrder"]))
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            raise ErrorPasarela(f"No se pudo consultar el pago en Flow: {error}") from error


def obtener_pasarela(nombre: str) -> PasarelaPago:
    pasarelas = {"khipu": KhipuGateway, "flow": FlowGateway}
    clase = pasarelas.get(nombre)
    if not clase:
        raise ValueError(f"Pasarela de pago desconocida: {nombre}")
    return clase()

# ---------- RF-27: confirmación de pagos ----------

def procesar_notificacion(nombre_pasarela: str, referencia: str) -> Suscripcion | None:
    """Confirma un pago avisado por la pasarela. Es idempotente.

    Busca la suscripción pendiente, consulta el estado real a la pasarela y
    activa el plan solo si el pago está aprobado, el monto coincide con el
    precio del plan y la orden corresponde a esa suscripción. Lanza
    ErrorPasarela si no se pudo consultar (la pasarela reintenta el aviso).
    """
    suscripcion = (
        Suscripcion.objects.select_related("plan", "usuario")
        .filter(referencia_pago=referencia, metodo_pago=nombre_pasarela)
        .first()
    )
    if suscripcion is None:
        return None
    if suscripcion.estado != Suscripcion.Estado.PENDIENTE:
        return suscripcion   # aviso repetido: ya se procesó
    estado = obtener_pasarela(nombre_pasarela).consultar_estado(referencia)
    orden_esperada = f"finmicro-{suscripcion.id}-"
    if not estado.orden.startswith(orden_esperada) or estado.monto != suscripcion.plan.precio_mensual_clp:
        logger.warning("Pago %s rechazado: orden o monto no coinciden (%s).", referencia, estado)
        return suscripcion
    if estado.pagado:
        activar_suscripcion_pagada(suscripcion)
    return suscripcion


@transaction.atomic
def activar_suscripcion_pagada(suscripcion: Suscripcion, ahora=None) -> Suscripcion:
    """Activa un período pagado. Si ya tenía Premium vigente, el período se suma al final (renovación)."""
    from core.auditoria import Accion, registrar

    ahora = ahora or timezone.now()
    suscripcion = Suscripcion.objects.select_for_update().get(pk=suscripcion.pk)
    if suscripcion.estado == Suscripcion.Estado.ACTIVA:
        return suscripcion
    vigentes = Suscripcion.objects.select_for_update().filter(
        usuario=suscripcion.usuario, estado=Suscripcion.Estado.ACTIVA
    )
    inicio_periodo = max(
        [ahora] + [s.fecha_fin for s in vigentes if s.plan_id == suscripcion.plan_id and s.fecha_fin]
    )
    vigentes.update(estado=Suscripcion.Estado.CANCELADA)
    suscripcion.estado = Suscripcion.Estado.ACTIVA
    suscripcion.fecha_inicio = ahora
    suscripcion.fecha_fin = inicio_periodo + DURACION_PERIODO
    suscripcion.save(update_fields=["estado", "fecha_inicio", "fecha_fin"])
    registrar(
        Accion.PAGO, usuario=suscripcion.usuario,
        detalle=f"{suscripcion.plan.nombre} pagado con {suscripcion.metodo_pago} hasta {suscripcion.fecha_fin:%d-%m-%Y}",
    )
    return suscripcion


def cambiar_a_basico(usuario, request=None) -> Suscripcion:
    from core.auditoria import Accion, registrar

    with transaction.atomic():
        Suscripcion.objects.filter(usuario=usuario, estado=Suscripcion.Estado.ACTIVA).update(
            estado=Suscripcion.Estado.CANCELADA
        )
        suscripcion = Suscripcion.objects.create(
            usuario=usuario, plan=Plan.objects.get(codigo=Plan.Codigo.BASICO), estado=Suscripcion.Estado.ACTIVA
        )
    registrar(Accion.CAMBIO_PLAN, request=request, usuario=usuario, detalle="Cambio a Plan Básico")
    return suscripcion


# ---------- RF-28: renovación y vencimiento ----------

NINGUNA, AVISAR, GRACIA, VENCER = "ninguna", "avisar", "gracia", "vencer"


def evaluar_renovacion(fecha_fin: date | None, hoy: date, dias_aviso=DIAS_AVISO_VENCIMIENTO, dias_gracia=DIAS_GRACIA):
    """Qué hacer hoy con una suscripción activa que cubre hasta `fecha_fin` (inclusive).

    Sin fecha de término (Plan Básico) no se hace nada.
    """
    if fecha_fin is None:
        return NINGUNA
    dias = (fecha_fin - hoy).days
    if dias > dias_aviso:
        return NINGUNA
    if dias >= 0:
        return AVISAR
    if -dias <= dias_gracia:
        return GRACIA
    return VENCER


def vencer_suscripcion(suscripcion: Suscripcion) -> None:
    """Termina un Premium impago y vuelve al Plan Básico (RN-03: nadie queda sin plan)."""
    from core.auditoria import Accion, registrar

    with transaction.atomic():
        suscripcion.estado = Suscripcion.Estado.VENCIDA
        suscripcion.save(update_fields=["estado"])
        asegurar_plan_basico(suscripcion.usuario)
    registrar(Accion.VENCIMIENTO_PLAN, usuario=suscripcion.usuario, detalle=f"{suscripcion.plan.nombre} vencido")
