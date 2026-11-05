"""
Segmentación gratuito / premium del módulo Educativo.

El plan vive en el perfil de la usuaria (usuarios.PerfilUsuaria.plan);
`es_premium` es verdadero para los planes premium y hospital. El contenido o
ejercicio marcado como premium se sigue listando para las usuarias gratuitas
(para que sepan que existe), pero sin su cuerpo, instrucciones ni enlace, y no
se puede completar.
"""


def usuaria_es_premium(usuario):
    """Si la usuaria tiene acceso premium. Sin perfil, se trata como gratuita."""
    perfil = getattr(usuario, 'perfil', None)
    return bool(perfil and perfil.es_premium)


def premium_de_la_peticion(request):
    """Igual que `usuaria_es_premium`, calculado una sola vez por petición."""
    if request is None:
        return False
    if not hasattr(request, '_educativo_es_premium'):
        request._educativo_es_premium = usuaria_es_premium(request.user)
    return request._educativo_es_premium


def esta_bloqueado(item, es_premium):
    """Un contenido o ejercicio premium está bloqueado para una usuaria gratuita."""
    return bool(getattr(item, 'es_premium', False)) and not es_premium


MENSAJE_PREMIUM = 'Este recurso es parte de Premium.'
