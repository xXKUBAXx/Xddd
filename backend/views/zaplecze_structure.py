from django.shortcuts import get_object_or_404
from ..models import Zaplecze, Account
from ..serializers import ZapleczeSerializer, StructireSerializer, CategorySerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse

from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.wp_api import WP_API


class ZapleczeAPIStructure(APIView):
    serializer_class = ZapleczeSerializer
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None
        
    @swagger_auto_schema(
            operation_description="Get Zaplecze categories", 
            responses={200:CategorySerializer, 400:"Bad Request"}
            )
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
        
    @swagger_auto_schema(
            operation_description="Create categories on Zaplecze", 
            request_body=StructireSerializer,
            responses={201:CategorySerializer}
            )
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)

        serializer = ZapleczeSerializer(zaplecze)

        data = serializer.data

        if "topic" in request.data:
            topic = request.data.get("topic")
            data["topic"] = topic
            serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
            if serializer.is_valid():
                serializer.save()
        else:
            topic = serializer.data["topic"]

        o = OpenAI_article(
            api_key=request.data.get("openai_api_key"),
            domain_name=data['domain'],
            wp_login=data['wp_user'],
            wp_pass=data['wp_api_key'],
            lang=data['lang']
        )

        structure, tokens = o.create_structure(topic, request.data.get('cat_num'), request.data.get('subcat_num'))

        account = get_object_or_404(Account, user_id=request.user.id)
        account.tokens_used += tokens
        account.save()

        return Response({"data": structure, "tokens": tokens}, status=status.HTTP_201_CREATED)



class AnyZapleczeAPIStructure(APIView):
    @swagger_auto_schema(
            operation_description="Create categories on Zaplecze", 
            request_body=StructireSerializer,
            responses={201:CategorySerializer}
            )
    def post(self, request):
        o = OpenAI_article(
            api_key=request.data.get("openai_api_key"),
            domain_name=request.data.get('domain'),
            wp_login=request.data.get('wp_user'),
            wp_pass=request.data.get('wp_api_key'),
            lang=request.data.get('lang')
        )

        structure, tokens = o.create_structure(request.data.get("topic"), request.data.get('cat_num'), request.data.get('subcat_num'))

        account = get_object_or_404(Account, user_id=request.user.id)
        account.tokens_used += tokens
        account.save()

        return Response({"data": structure, "tokens": tokens}, status=status.HTTP_201_CREATED)