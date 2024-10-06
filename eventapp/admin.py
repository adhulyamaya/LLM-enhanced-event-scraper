from django.contrib import admin
from .models import EntitiesMaster

@admin.register(EntitiesMaster)
class EntitiesMasterAdmin(admin.ModelAdmin):
    list_display = ('auditorium', 'program_name', 'date_time')
    search_fields = ('auditorium', 'program_name')
   