import os
import uuid
import warnings

from io import BytesIO

from urllib.parse import quote

from urllib.request import Request, urlopen

from urllib.error import HTTPError, URLError

from PIL import (
    Image,
    ImageOps,
    UnidentifiedImageError
)
from pathlib import Path

from dotenv import dotenv_values


# =====================================================
# CONFIGURACION
# =====================================================

MAX_INPUT_BYTES = 20 * 1024 * 1024

# Dejamos margen frente al limite de 500 KB del bucket.
MAX_OUTPUT_BYTES = 480 * 1024

MAX_IMAGE_PIXELS = 40_000_000

BUCKET_DEFAULT = "productos"


# =====================================================
# EXCEPCIONES
# =====================================================

class ImageValidationError(ValueError):
    pass


class StorageConfigurationError(RuntimeError):
    pass


class StorageUploadError(RuntimeError):
    pass


# =====================================================
# LECTURA ROBUSTA DE VARIABLES DE STORAGE
# =====================================================

def _leer_variable_storage(*nombres):

    # 1. Variables del proceso: Render o entorno local.
    for nombre in nombres:

        valor = os.environ.get(nombre)

        if valor and str(valor).strip():
            return str(valor).strip()

    # 2. Archivos .env posibles.
    backend_dir = Path(__file__).resolve().parents[1]

    proyecto_dir = backend_dir.parent

    archivos_env = (
        backend_dir / ".env",
        proyecto_dir / ".env"
    )

    for archivo in archivos_env:

        if not archivo.is_file():
            continue

        variables = dotenv_values(archivo)

        for nombre in nombres:

            valor = variables.get(nombre)

            if valor and str(valor).strip():
                return str(valor).strip()

    return ""


# =====================================================
# OPTIMIZAR IMAGEN
# =====================================================

def optimizar_imagen_webp(archivo):

    if archivo is None:

        raise ImageValidationError(
            "No se recibió ninguna imagen."
        )

    contenido_original = archivo.stream.read(
        MAX_INPUT_BYTES + 1
    )

    if not contenido_original:

        raise ImageValidationError(
            "El archivo está vacío."
        )

    if len(contenido_original) > MAX_INPUT_BYTES:

        raise ImageValidationError(
            "La imagen original supera el límite de 20 MB."
        )

    try:

        with warnings.catch_warnings():

            warnings.simplefilter(
                "error",
                Image.DecompressionBombWarning
            )

            with Image.open(
                BytesIO(contenido_original)
            ) as origen:

                formato = origen.format

                formatos_permitidos = {
                    "JPEG",
                    "PNG",
                    "WEBP"
                }

                if formato not in formatos_permitidos:

                    raise ImageValidationError(
                        "Formato no permitido. "
                        "Utilice JPG, PNG o WebP."
                    )

                if getattr(origen, "is_animated", False):

                    raise ImageValidationError(
                        "No se permiten imágenes animadas."
                    )

                if (
                    origen.width * origen.height
                    > MAX_IMAGE_PIXELS
                ):

                    raise ImageValidationError(
                        "La resolución de la imagen es demasiado grande."
                    )

                tiene_transparencia = (
                    "A" in origen.getbands()
                    or "transparency" in origen.info
                )

                imagen = ImageOps.exif_transpose(
                    origen
                )

                imagen.load()

                imagen = imagen.convert(
                    "RGBA"
                    if tiene_transparencia
                    else "RGB"
                )

    except ImageValidationError:

        raise

    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning
    ) as error:

        raise ImageValidationError(
            "La imagen tiene una resolución no permitida."
        ) from error

    except (
        UnidentifiedImageError,
        OSError
    ) as error:

        raise ImageValidationError(
            "El archivo no es una imagen válida o está dañado."
        ) from error

    # =================================================
    # COMPRESION PROGRESIVA
    # =================================================

    dimensiones = (
        1600,
        1400,
        1200,
        1000,
        850,
        700,
        560,
        450,
        360
    )

    calidades = (
        84,
        80,
        76,
        72,
        68,
        64,
        60,
        56,
        52,
        48,
        44
    )

    for dimension in dimensiones:

        candidata = imagen.copy()

        candidata.thumbnail(
            (dimension, dimension),
            Image.Resampling.LANCZOS
        )

        for calidad in calidades:

            salida = BytesIO()

            candidata.save(
                salida,
                format="WEBP",
                quality=calidad,
                method=6
            )

            contenido = salida.getvalue()

            if len(contenido) <= MAX_OUTPUT_BYTES:

                return contenido

    raise ImageValidationError(
        "No fue posible reducir la imagen por debajo de 480 KB. "
        "Pruebe con otra fotografía."
    )


# =====================================================
# SUBIR A SUPABASE STORAGE
# =====================================================

def subir_imagen_catalogo(archivo):

    # ================================================
    # VALIDAR CONFIGURACION
    # ================================================

    supabase_url = _leer_variable_storage(
        "SUPABASE_URL"
    ).rstrip("/")

    api_key = _leer_variable_storage(
        "SUPABASE_SECRET_KEY",
        "SUPABASE_SERVICE_ROLE_KEY"
    )

    bucket = _leer_variable_storage(
        "SUPABASE_STORAGE_BUCKET"
    ) or BUCKET_DEFAULT


    faltantes = []

    if not supabase_url:
        faltantes.append("SUPABASE_URL")

    if not api_key:
        faltantes.append(
            "SUPABASE_SECRET_KEY "
            "(o SUPABASE_SERVICE_ROLE_KEY)"
        )

    if faltantes:

        raise StorageConfigurationError(
            "Faltan variables de Supabase: "
            + ", ".join(faltantes)
            + ". Revisa backend/.env o las variables "
            "del entorno de ejecución."
        )

    if not bucket:

        raise StorageConfigurationError(
            "SUPABASE_STORAGE_BUCKET no está configurada."
        )

    if not supabase_url or not api_key:

        raise StorageConfigurationError(
            "Falta configurar SUPABASE_URL "
            "o la clave secreta de Supabase."
        )

    if not bucket:

        raise StorageConfigurationError(
            "El nombre del bucket no está configurado."
        )

    # ================================================
    # COMPRIMIR
    # ================================================

    contenido = optimizar_imagen_webp(
        archivo
    )

    # ================================================
    # GENERAR NOMBRE UNICO
    # ================================================

    nombre_archivo = (
        f"{uuid.uuid4().hex}.webp"
    )

    ruta_storage = (
        f"catalogo/items/{nombre_archivo}"
    )

    bucket_encoded = quote(
        bucket,
        safe=""
    )

    path_encoded = quote(
        ruta_storage,
        safe="/"
    )

    endpoint = (
        f"{supabase_url}"
        f"/storage/v1/object/"
        f"{bucket_encoded}/"
        f"{path_encoded}"
    )

    # ================================================
    # HEADERS
    # ================================================

    headers = {

        "apikey": api_key,

        "Content-Type": "image/webp",

        "Cache-Control": "max-age=31536000",

        "x-upsert": "false"

    }

    # Compatibilidad con la antigua clave JWT service_role.
    # Las nuevas claves sb_secret_ no son JWT y no deben
    # enviarse como Bearer.
    if api_key.startswith("eyJ"):

        headers["Authorization"] = (
            f"Bearer {api_key}"
        )

    # ================================================
    # SUBIR OBJETO
    # ================================================

    solicitud = Request(

        endpoint,

        data=contenido,

        headers=headers,

        method="POST"

    )

    try:

        with urlopen(
            solicitud,
            timeout=30
        ) as respuesta:

            if respuesta.status not in (200, 201):

                raise StorageUploadError(
                    "Supabase no confirmó la carga de la imagen."
                )

    except HTTPError as error:

        detalle = error.read(
            1000
        ).decode(
            "utf-8",
            errors="replace"
        )

        raise StorageUploadError(
            f"Supabase Storage respondió HTTP {error.code}: {detalle}"
        ) from error

    except URLError as error:

        raise StorageUploadError(
            "No fue posible conectar con Supabase Storage."
        ) from error

    # ================================================
    # URL PUBLICA
    # ================================================

    url_publica = (
        f"{supabase_url}"
        f"/storage/v1/object/public/"
        f"{bucket_encoded}/"
        f"{path_encoded}"
    )

    return {

        "url": url_publica,

        "path": ruta_storage,

        "size_bytes": len(contenido),

        "content_type": "image/webp"

    }