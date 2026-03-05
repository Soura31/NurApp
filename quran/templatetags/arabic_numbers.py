from django import template

register = template.Library()

_WESTERN = "0123456789"
_ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"
_TRANS = str.maketrans(_WESTERN, _ARABIC_INDIC)


@register.filter
def arabic_digits(value):
    if value is None:
        return ""
    return str(value).translate(_TRANS)

