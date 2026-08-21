from django.contrib import admin
from .models import Goal


# Registering Goal makes it visible and editable in /admin
admin.site.register(Goal)