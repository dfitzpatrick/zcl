from django.dispatch import Signal

new_webhook = Signal(providing_args=['sub'])
webhook_update = Signal(providing_args=['webhook_name', 'uuid', 'data'])