from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.response import Response
from rest_framework.views import APIView


class ZapleczeAPIView(APIView):
    
    def get(self, request, *args, **kwargs):
        zaplecza = Zaplecze.objects.all()
        serializer = ZapleczeSerializer(zaplecza, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data = {
            'domain':request.data.get('domain'),
            'url': request.data.get('url'),
            'login': request.data.get('login'),
            'password': request.data.get('password'),
            'lang': request.data.get('lang'),
            'topic': request.data.get('topic')
        }

        serializer = ZapleczeSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    