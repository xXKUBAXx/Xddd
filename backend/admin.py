from django.contrib import admin
from .models import Zaplecze, Account, Link, Banner, ZapleczeCategory
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
# Register your models here.

admin.site.register(ZapleczeCategory)

class ZapleczeAdmin(admin.ModelAdmin):
    list_display = ['domain', 'email', 'url', 'login', 'password', 'topic']

admin.site.register(Zaplecze, ZapleczeAdmin)


class LinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'keyword', 'link', 'url', 'done']

admin.site.register(Link, LinkAdmin)


class BannerAdmin(admin.ModelAdmin):
    list_display = ['active', 'text', 'color']

admin.site.register(Banner, BannerAdmin)


class AccountInline(admin.StackedInline):
    model = Account
    can_delete = False
    verbose_name_plural = 'Accounts'

class CustomUserAdmin(UserAdmin):
    inlines = (AccountInline, )

class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'tokens_used', 'USD', 'openai_api_key', 'semstorm_api_key')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# admin.site.register(Account)
admin.site.register(Account, AccountAdmin)