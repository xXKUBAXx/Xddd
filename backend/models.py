from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm


class ZapleczeCategory(models.Model):
    name = models.CharField(max_length=256, unique=True)
    
    def __str__(self):
        return self.name


class Zaplecze(models.Model):
    #basic
    domain = models.CharField(max_length=64, blank=True, null=True, unique=True)
    email = models.CharField(max_length=64, blank=True, null=True)

    #Admin
    url = models.CharField(max_length=64, blank=True, null=True)
    login = models.CharField(max_length=64, blank=True, null=True)
    password = models.CharField(max_length=64, blank=True, null=True)

    #WP Create
    ftp_user = models.CharField(max_length=64, blank=True, null=True)
    ftp_pass = models.CharField(max_length=64, blank=True, null=True)
    db_user = models.CharField(max_length=64, blank=True, null=True)
    db_pass = models.CharField(max_length=64, blank=True, null=True)

    #WP API stuff
    lang = models.CharField(max_length=4, blank=True, null=True)
    topic = models.CharField(max_length=128, blank=True, null=True)
    wp_user = models.CharField(max_length=32, blank=True, null=True)
    wp_password = models.CharField(max_length=64, blank=True, null=True)
    wp_api_key = models.CharField(max_length=128, blank=True, null=True)

    #Website stats
    category = models.ForeignKey(ZapleczeCategory, blank=True, null=True, on_delete=models.DO_NOTHING) 
    wp_post_count = models.IntegerField(default=0, null=True, blank=True)
    wp_category_count = models.IntegerField(default=0, null=True, blank=True)
    wp_last_edit = models.DateField(blank=True, null=True)
    linked_websites = models.IntegerField(default=0)
    outgoing_links = models.IntegerField(default=0)
    semstorm_top10 = models.IntegerField(default=0)
    semstorm_top10prev = models.IntegerField(default=0)
    semstorm_top50 = models.IntegerField(default=0)
    semstorm_top50prev = models.IntegerField(default=0)

    #Zaplecze health
    domain_ip = models.CharField(max_length=32, blank=True, null=True)
    domain_status_code = models.IntegerField(null=True, blank=True)
    ssl_active = models.BooleanField(null=True, blank=True)
    ssl_expiration_date = models.DateField(null=True, blank=True)
    domain_creation = models.DateField(null=True, blank=True)
    domain_expiration = models.DateField(null=True, blank=True)
    domain_registrar = models.CharField(max_length=256, blank=True, null=True)
    domain_servername = models.CharField(max_length=128, blank=True, null=True)

class Link(models.Model):
    task_id = models.IntegerField(default=0)
    ul_id = models.CharField(max_length=32, default="client0")
    user = models.CharField(max_length=64)
    domain = models.CharField(max_length=64)
    link = models.CharField(max_length=256)
    keyword = models.CharField(max_length=128)
    url = models.CharField(max_length=128, blank=True, null=True)
    cost = models.IntegerField(blank=True, null=True)
    done = models.BooleanField()


class Banner(models.Model):
    text = models.CharField(max_length = 2048)
    active = models.BooleanField(default=True)
    color = models.CharField(max_length = 32, default="#add8e6")

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    openai_api_key = models.CharField(max_length=64, default="", blank=True, null=True)
    semstorm_api_key = models.CharField(max_length=64, default="", blank=True, null=True)
    tokens_used = models.IntegerField(default=0)
    USD = models.FloatField(default=0.0)
    cursor_followed = models.BooleanField(default=False)
    premium_user = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username