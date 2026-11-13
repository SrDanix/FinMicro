"""RF-29: versión 1.0 de los términos y de la política de privacidad.

Texto en borrador, pendiente de revisión por la asesoría legal del
proyecto. Para cambiarlo se publica una versión nueva desde el
administrador; los usuarios deberán aceptarla al volver a entrar.
"""
import hashlib

from django.db import migrations

TERMINOS = """Términos y condiciones de FinMicro · versión 1.0

Borrador sujeto a revisión de la asesoría legal del proyecto.

1. El servicio. FinMicro es una plataforma web que ayuda a microempresarios a registrar ingresos y gastos, estimar impuestos y proyectar su negocio. Las calculadoras y estimaciones son una herramienta de apoyo: no constituyen asesoría tributaria, contable ni financiera. Antes de declarar, valida siempre los resultados en sii.cl o con un contador.

2. Tu cuenta. Debes entregar datos verdaderos, en especial tu RUT, y cuidar tu contraseña. Eres responsable de lo que se registre con tu cuenta y de los accesos que otorgues a colaboradores.

3. Planes y pagos. El Plan Básico es gratuito, tiene publicidad y un límite de movimientos mensuales. El Plan Premium se paga por mes mediante Khipu o Flow.cl, sin renovación automática: puedes renovarlo antes de su vencimiento. Si no lo renuevas, tienes tres días de gracia y luego vuelves al Plan Básico sin perder tus datos.

4. Uso permitido. No puedes usar FinMicro para fines ilícitos, intentar acceder a datos de otros negocios ni afectar el funcionamiento del servicio.

5. Disponibilidad. Hacemos lo razonable para que el servicio esté disponible y respaldado, pero puede haber interrupciones por mantenimiento o fallas.

6. Término. Puedes descargar tus datos y eliminar tu cuenta cuando quieras desde "Mi perfil". Podemos suspender cuentas que infrinjan estos términos.

7. Cambios. Si cambiamos estos términos publicaremos una nueva versión y te pediremos aceptarla al volver a entrar.

8. Ley aplicable. Estos términos se rigen por la ley chilena, incluida la Ley N.º 19.496 sobre protección de los derechos de los consumidores.
"""

PRIVACIDAD = """Política de privacidad de FinMicro · versión 1.0

Borrador sujeto a revisión de la asesoría legal del proyecto.

1. Qué datos tratamos. Los que entregas al registrarte (usuario, correo, RUT, nombre y rubro del negocio, teléfono y comuna), tu configuración tributaria y los movimientos, productos y categorías que registras. También registramos inicios de sesión y acciones sensibles con su fecha e IP, por seguridad.

2. Para qué. Para prestarte el servicio: calcular tus indicadores, impuestos estimados y proyecciones, enviarte avisos (vencimientos, estado de tu plan, recuperación de contraseña) y proteger tu cuenta. No vendemos ni cedemos tus datos para publicidad.

3. Base legal. Tu consentimiento, que registramos con fecha y versión de este documento, y la ejecución del servicio que contratas, conforme a la Ley N.º 19.628 sobre protección de la vida privada y sus modificaciones (Ley N.º 21.719).

4. Con quién se comparten. Solo con proveedores necesarios para operar: alojamiento en Amazon Web Services, la pasarela de pago que elijas (Khipu o Flow.cl) y el servicio de envío de correos. Ellos tratan los datos por encargo nuestro. Los colaboradores que tú invites ven los datos de tu negocio según el rol que les des.

5. Tus derechos. Puedes acceder a tus datos y descargarlos en formato JSON, corregirlos y eliminarlos junto con tu cuenta desde "Mi perfil". También puedes oponerte a un tratamiento o pedir información escribiendo al equipo de FinMicro.

6. Conservación. Guardamos tus datos mientras tengas una cuenta. Al eliminarla se borran de forma permanente, salvo el registro mínimo de auditoría (nombre de usuario, acción, fecha e IP) que se conserva por seguridad.

7. Seguridad. Las contraseñas se guardan cifradas con un algoritmo de una vía, la comunicación viaja cifrada (HTTPS) y cada negocio solo puede ver sus propios datos o aquellos a los que fue invitado.
"""

DOCUMENTOS = [("terminos", TERMINOS), ("privacidad", PRIVACIDAD)]


def publicar(apps, schema_editor):
    DocumentoLegal = apps.get_model("accounts", "DocumentoLegal")
    for tipo, contenido in DOCUMENTOS:
        DocumentoLegal.objects.get_or_create(
            tipo=tipo, version="1.0",
            defaults={"contenido": contenido, "huella": hashlib.sha256(contenido.encode("utf-8")).hexdigest()},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_documentos_legales"),
    ]

    operations = [
        migrations.RunPython(publicar, migrations.RunPython.noop),
    ]
