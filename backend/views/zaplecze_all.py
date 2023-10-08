from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema


class ZapleczeAPIView(APIView):
    
    serializer_class = ZapleczeSerializer
    @swagger_auto_schema(
            operation_description="Get data of all Zaplecza", 
            responses={201:ZapleczeSerializer, 400:"Bad Request"}
            )
    def get(self, request, *args, **kwargs):
        zaplecza = Zaplecze.objects.all()
        serializer = ZapleczeSerializer(zaplecza, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
            operation_description="Create new Zaplecze", 
            request_body=ZapleczeSerializer, 
            responses={201:ZapleczeSerializer, 400:"Bad Request"}
            )
    def post(self, request, *args, **kwargs):
        data = {
            'domain':request.data.get('domain'),
            'url': request.data.get('url'),
            'login': request.data.get('login'),
            'password': request.data.get('password'),
            'lang': request.data.get('lang'),
            'email': request.data.get('email')
        }

        serializer = ZapleczeSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    