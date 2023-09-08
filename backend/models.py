from django.db import models


class Zaplecze(models.Model):
    #basic
    domain = models.CharField(max_length=64, blank=True, null=True)
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
    topic = models.CharField(max_length=32, blank=True, null=True)
    wp_user = models.CharField(max_length=32, blank=True, null=True)
    wp_password = models.CharField(max_length=64, blank=True, null=True)
    wp_api_key = models.CharField(max_length=128, blank=True, null=True)