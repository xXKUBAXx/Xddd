from django.contrib import admin
from .models import Zaplecze
# Register your models here.


class ZapleczeAdmin(admin.ModelAdmin):
    list_display = ['domain', 'email', 'url', 'login', 'password', 'topic']


admin.site.register(Zaplecze, ZapleczeAdmin)