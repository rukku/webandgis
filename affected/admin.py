from django.contrib import admin
from affected.models import Affected

class AffectedAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Affected)
