from django import template  
  
register = template.Library()  
  
@register.filter(name='add_attributes')  
def add_attributes(field, args):  
    # Split the arguments by commas  
    attrs = {}  
    for arg in args.split(','):  
        # Split key and value  
        key_value = arg.strip().split('=')  
        if len(key_value) == 2:  
            key, value = key_value  
            attrs[key.strip()] = value.strip()  
        elif len(key_value) == 1:  
            # For arguments like 'required'  
            attrs[key_value[0].strip()] = True  
    return field.as_widget(attrs=attrs)  