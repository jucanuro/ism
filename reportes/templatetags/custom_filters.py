from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """
    Obtiene un atributo de un objeto dinámicamente.
    Uso: {{ objeto|getattr:nombre_atributo }}
    """
    return getattr(obj, attr, '') # Devuelve una cadena vacía si el atributo no se encuentra