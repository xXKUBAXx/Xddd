from django.shortcuts import get_object_or_404
from ..models import Zaplecze, Account
from ..serializers import ZapleczeSerializer, StructireSerializer, CategorySerializer
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse
from asgiref.sync import sync_to_async


from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.wp_api import WP_API

from .zaplecze_api import ZAPIView


class ZapleczeAPIStructure(ZAPIView):
    serializer_class = ZapleczeSerializer
    throttle_scope = 'structure'
    async def get_object(self, zaplecze_id):
        try:
            return await sync_to_async(Zaplecze.objects.get, thread_sensitive=False)(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None
        
    @swagger_auto_schema(
            operation_description="Get Zaplecze categories", 
            responses={200:CategorySerializer, 400:"Bad Request"}
            )
    async def get(self, request, zaplecze_id):
        zaplecze = await self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with todo id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        try:
            wp_api = WP_API(data['domain'], data['wp_user'], data['wp_api_key'])
        except Exception as e:
            return Response({"data": str(e), "tokens": 0}, status=status.HTTP_400_BAD_REQUEST)

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
    async def post(self, request, zaplecze_id):
        zaplecze = await self.get_object(zaplecze_id)

        serializer = ZapleczeSerializer(zaplecze)

        data = serializer.data
        self.logger.info(f"{request.user.email} - Generating {int(request.data.get('cat_num'))*int(request.data.get('subcat_num'))} categories at {data['domain']}")        

        if "topic" in request.data:
            topic = request.data.get("topic")
            data["topic"] = topic
            serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
            if await sync_to_async(serializer.is_valid, thread_sensitive=False)():
                sync_to_async(serializer.save, thread_sensitive=False)()
        else:
            topic = serializer.data["topic"]

        try:
            o = OpenAI_article(
                api_key=request.data.get("openai_api_key"),
                domain_name=data['domain'],
                wp_login=data['wp_user'],
                wp_pass=data['wp_api_key'],
                lang=data['lang']
            )
        except Exception as e:
            return Response({"data": str(e), "tokens": 0}, status=status.HTTP_400_BAD_REQUEST)


        structure, tokens = await o.create_structure(topic, request.data.get('cat_num'), request.data.get('subcat_num'))

        account = await sync_to_async(get_object_or_404, thread_sensitive=False)(Account, user_id=request.user.id)
        account.tokens_used += tokens
        await sync_to_async(account.save,thread_sensitive=False)()

        self.logger.info(f"{request.user.email} - Done generating {int(request.data.get('cat_num'))*int(request.data.get('subcat_num'))} categories at {data['domain']}")        
        return Response({"data": structure, "tokens": tokens}, status=status.HTTP_201_CREATED)



class AnyZapleczeAPIStructure(ZAPIView):
    @swagger_auto_schema(
            operation_description="Create categories on Zaplecze", 
            request_body=StructireSerializer,
            responses={201:CategorySerializer}
            )
    async def post(self, request):
        self.logger.info(f"{request.user.email} - Generating {int(request.data.get('cat_num'))*int(request.data.get('subcat_num'))} categories at {request.data.get('domain')}")        
        o = OpenAI_article(
            api_key=request.data.get("openai_api_key"),
            domain_name=request.data.get('domain'),
            wp_login=request.data.get('wp_user'),
            wp_pass=request.data.get('wp_api_key'),
            lang=request.data.get('lang')
        )

        structure, tokens = await o.create_structure(request.data.get("topic"), request.data.get('cat_num'), request.data.get('subcat_num'))
        self.add_tokens(request.user.id, tokens, request.data.get("openai_api_key"))

        account = await sync_to_async(get_object_or_404, thread_sensitive=False)(Account, user_id=request.user.id)
        account.tokens_used += tokens
        await sync_to_async(account.save,thread_sensitive=False)()

        self.logger.info(f"{request.user.email} - Done generating {int(request.data.get('cat_num'))*int(request.data.get('subcat_num'))} categories at {request.data.get('domain')}")        
        return Response({"data": structure, "tokens": tokens}, status=status.HTTP_201_CREATED)