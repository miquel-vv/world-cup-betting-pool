from django import template

register = template.Library()

@register.filter
def replace_spaces(text):
    return text.replace(' ', '_')