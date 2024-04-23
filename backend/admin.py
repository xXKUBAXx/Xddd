from django.contrib import admin
from .models import Zaplecze, Account, Link, Banner, ZapleczeCategory, CeneoFiles, vdTarget, primislaoDomains, primislaoLinks
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
# Register your models here.

admin.site.register(ZapleczeCategory)

admin.site.register(CeneoFiles)


class vdTargetAdmin(admin.ModelAdmin):
    list_display = ['server_name', 'plugin_domain']
admin.site.register(vdTarget, vdTargetAdmin)

class primislaoDomainsAdmin(admin.ModelAdmin):
    list_display = ['domain_name', 'server_name']
admin.site.register(primislaoDomains, primislaoDomainsAdmin)

class primislaoOutgoingLinks(admin.ModelAdmin):
    list_display = ['task_id', 'user', 'link_domain', 'target_domain', 'anchor', 'nofollow', 'limit', 'link_id', 'link_data']
admin.site.register(primislaoLinks, primislaoOutgoingLinks)

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