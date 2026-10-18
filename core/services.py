"""
Integración con indicadores económicos oficiales de Chile (UF, IPC, etc.)

Sección III del informe (PESTEL, factor TECNOLÓGICO): "APIs abiertas del
Banco Central de Chile". La API oficial del Banco Central
(https://si3.bcentral.cl) requiere credenciales de usuario registrado.
Como alternativa gratuita y sin autenticación —muy usada en proyectos
chilenos— se usa mindicador.cl, que publica los mismos indicadores (UF,
IPC, UTM, dólar, etc.) tomándolos del Banco Central. Doc: https://mindicador.cl/

Todo el acceso a la red vive en esta clase (patrón adaptador): si más
adelante se contratan credenciales de la API oficial del Banco Central,
solo se reescribe esta clase — el resto de la aplicación no cambia.
"""
import requests
from django.core.cache import cache


class BancoCentralService:
    BASE_URL = "https://mindicador.cl/api"
    TIMEOUT = 6
    # Estos indicadores se actualizan como máximo una vez al día: no
    # tiene sentido golpear la API externa en cada request.
    CACHE_TTL_SEGUNDOS = 60 * 60 * 6

    INDICADORES_SOPORTADOS = {"uf", "ipc", "utm", "dolar", "euro", "ivp", "imacec", "tpm"}

    @classmethod
    def _get(cls, ruta: str = ""):
        url = f"{cls.BASE_URL}/{ruta}".rstrip("/")
        respuesta = requests.get(url, timeout=cls.TIMEOUT)
        respuesta.raise_for_status()
        return respuesta.json()

    @classmethod
    def indicadores_del_dia(cls) -> dict:
        """UF, IPC, UTM, dólar, etc. del día, con caché de 6 horas."""
        clave = "bcentral:indicadores_del_dia"
        datos = cache.get(clave)
        if datos is None:
            datos = cls._get()
            cache.set(clave, datos, cls.CACHE_TTL_SEGUNDOS)
        return datos

    @classmethod
    def valor_actual(cls, indicador: str):
        indicador = indicador.lower()
        if indicador not in cls.INDICADORES_SOPORTADOS:
            raise ValueError(f"Indicador no soportado: {indicador}")
        return cls.indicadores_del_dia().get(indicador)

    @classmethod
    def historial(cls, indicador: str) -> dict:
        """Serie del último mes para un indicador (uf, ipc, dolar, ...)."""
        indicador = indicador.lower()
        if indicador not in cls.INDICADORES_SOPORTADOS:
            raise ValueError(f"Indicador no soportado: {indicador}")
        clave = f"bcentral:historial:{indicador}"
        datos = cache.get(clave)
        if datos is None:
            datos = cls._get(indicador)
            cache.set(clave, datos, cls.CACHE_TTL_SEGUNDOS)
        return datos