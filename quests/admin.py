from django.contrib import admin
from .models import Quest

# Registering Quest makes it visible and editable in /admin
admin.site.register(Quest)
