from rest_framework import serializers
from .models import Zaplecze, Account


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
            "wp_api_key": {"required": False, "allow_null": True, "allow_blank": True},
            "wp_post_count": {"required": False, "allow_null": True}
            }


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class WriteSerializer(serializers.Serializer):
    categories = serializers.JSONField(default=1)
    openai_api_key = serializers.CharField(max_length=64)
    a_num = serializers.IntegerField(default=1)
    p_num = serializers.IntegerField(default=2)
    links = serializers.ListField(default=[])
    domain = serializers.CharField(max_length=32)
    lang = serializers.CharField(max_length=4, default="pl")
    wp_user = serializers.CharField(max_length=16)
    wp_api_key = serializers.CharField(required=False)
    wp_password = serializers.CharField(required=False)
    nofollow = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    days_delta = serializers.IntegerField(default=7)
    forward_delta = serializers.BooleanField(default=False)


    def validate(self, data):
        if not data['wp_api_key'] and not data['wp_password']:
            raise serializers.ValidationError("Need some password")


class StructireSerializer(serializers.Serializer):
    openai_api_key = serializers.CharField(max_length=64)
    topic = serializers.CharField()
    cat_num = serializers.IntegerField(default=1)
    subcat_num = serializers.IntegerField(default=1)


class CategorySerializer(serializers.Serializer):
    cateogires = serializers.ListField(child=serializers.JSONField())


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zaplecze
        fields = ["url"]
