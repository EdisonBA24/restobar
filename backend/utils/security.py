
from flask import session


# =====================================================
# VALIDAR USUARIO AUTENTICADO
# =====================================================

def tiene_sesion():

    return session.get("user_id") is not None


# =====================================================
# OBTENER PERFIL NORMALIZADO
# =====================================================

def obtener_perfil():

    return str(
        session.get("perfil") or ""
    ).strip().upper()


# =====================================================
# VALIDAR ADMINISTRADOR
#
# Acepta tanto:
# admin
# ADMIN
# Admin
#
# La autorización depende exclusivamente
# del perfil guardado en la sesión autenticada.
# =====================================================

def es_admin():

    return (
        tiene_sesion()
        and obtener_perfil() == "ADMIN"
    )


# =====================================================
# VALIDAR PERMISO DE MODIFICACION DE PRECIOS
# =====================================================

def puede_modificar_precios():

    return es_admin()
