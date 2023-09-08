from rest_framework import serializers
from .models import Zaplecze


class ZapleczeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zaplecze
        fields = '__all__'
        extra_kwargs = {
            "lang": {"required": False, "allow_null": True, "allow_blank": True},
            "topic": {"required": False, "allow_null": True, "allow_blank": True},
            "email": {"required": False, "allow_null": True, "allow_blank": True},
            "ftp_user": {"required": False, "allow_null": True, "allow_blank": True},
            "ftp_pass": {"required": False, "allow_null": True, "allow_blank": True},
            "db_user": {"required": False, "allow_null": True, "allow_blank": True},
            "db_pass": {"required": False, "allow_null": True, "allow_blank": True},
            "wp_user": {"required": False, "allow_null": True, "allow_blank": True},
            "wp_password": {"required": False, "allow_null": True, "allow_blank": True},
            "wp_api_key": {"required": False, "allow_null": True, "allow_blank": True}
            }
