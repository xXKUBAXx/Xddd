from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from django.views.generic import View


class ZapleczeAPIDetail(APIView):
    serializer_class = ZapleczeSerializer
    
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None
        
    @swagger_auto_schema(
            operation_description="Get Zaplecze data",
            responses={200:ZapleczeSerializer, 400:"Bad Request"}
            )
    def get(self, request, zaplecze_id, *args, **kwargs):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ZapleczeSerializer(zaplecze)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
            operation_description="Update Zaplecze data", 
            request_body=ZapleczeSerializer, 
            responses={200:ZapleczeSerializer, 400:"Bad Request"}
            )
    def put(self, request, zaplecze_id, *args, **kwargs):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ZapleczeSerializer(instance = zaplecze, data=request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
            operation_description="Delete Zaplecze", 
            responses={200:"Deleted", 400:"Bad Request"}
            )
    def delete(self, request, zaplecze_id, *args, **kwargs):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        zaplecze.delete()

        return Response(
            {"res": "Salto do śmieciary!"},
            status=status.HTTP_200_OK
        )
    
