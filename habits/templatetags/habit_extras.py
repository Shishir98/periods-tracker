from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def habit_status(grid, habit_id):
    if isinstance(grid, dict):
        return grid.get(habit_id, {})
    return {}