from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.http import JsonResponse

from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.wp_api import WP_API


class ZapleczeAPIStructure(APIView):
    
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None
        
    def get(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with todo id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        wp_api = WP_API(data['domain'], data['wp_user'], data['wp_api_key'])
        return JsonResponse(
            wp_api.get_categories(),
            status=status.HTTP_200_OK,
            safe=False
            )
        
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)

        serializer = ZapleczeSerializer(zaplecze)

        data = serializer.data

        if "topic" in request.data:
            topic = request.data.get("topic")
        else:
            topic = serializer.data["topic"]

        o = OpenAI_article(
            api_key=request.data.get("openai_api_key"),
            domain_name=data['domain'],
            wp_login=data['wp_user'],
            wp_pass=data['wp_api_key'],
            lang=data['lang']
        )

        structure = o.create_structure(topic, request.data.get('cat_num'), request.data.get('subcat_num'))

        return Response(structure, status=status.HTTP_201_CREATED)
