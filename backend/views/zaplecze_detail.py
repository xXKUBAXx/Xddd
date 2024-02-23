from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from django.db import IntegrityError
from backend.src.CreateWPblog.wp_api import WP_API
from backend.src.CreateWPblog.setup_wp import Setup_WP
import ssl
import socket
import requests
import datetime


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


    def post(self, request, *args, **kwargs):
        try:
            z = Zaplecze(**request.data)
            z.save()
        except IntegrityError:
            return Response({"res": "This domain already exists in database"}, status=status.HTTP_400_BAD_REQUEST)
        print(request.data)
        return Response(request.data, status=status.HTTP_201_CREATED)
    
    
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
    

class ZapleczeHealth(APIView):
    serializer_class = ZapleczeSerializer

    def check_ssl(self, domain):
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                try:
                    cert = ssock.getpeercert()
                    return True, datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').strftime("%Y-%m-%d")

                except:
                    return False, datetime.date.today()


    def post(self, request, id):
        try:
            zaplecze =  Zaplecze.objects.get(id=id)
        except Zaplecze.DoesNotExist:
            return Response({"res": "This zaplecze does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not zaplecze.domain_ip:
            try:
                zaplecze.domain_ip = socket.gethostbyname(zaplecze.domain)
                zaplecze.save()
            except:
                print("IP unreachable")
        
        try:
            zaplecze.domain_status_code = requests.get("https://"+zaplecze.domain).status_code
        except:
            zaplecze.domain_status_code = requests.get("http://"+zaplecze.domain).status_code
        zaplecze.save()

        try:
            zaplecze.ssl_active, zaplecze.ssl_expiration_date = self.check_ssl(zaplecze.domain)
        except:
            zaplecze.ssl_active = False
        zaplecze.save()

        try:
            response = requests.get(
                url="https://api.api-ninjas.com/v1/whois?domain="+zaplecze.domain, 
                headers={"X-Api-Key": "ty5dkesssA9wHIteFlOK7w==hhRH0WN9hHaNIiwH"}
                ).json()
        except:
            print("Ninjas WhoIs API unreachable")
        try:
            zaplecze.domain_creation, zaplecze.domain_expiration, zaplecze.domain_registrar, zaplecze.domain_servername = \
                datetime.datetime.fromtimestamp(response["creation_date"]).date(), \
                datetime.datetime.fromtimestamp(response["expiration_date"]).date(), \
                response["registrar"], \
                response["name_servers"]
            zaplecze.save()
        except:
            print("Ninjas WhoIs API incomplete data")

        if not zaplecze.wp_api_key and zaplecze.wp_password:
            setup = Setup_WP(zaplecze.domain)
            zaplecze.wp_api_key = setup.get_api_key(zaplecze.login, zaplecze.password)
        
        if zaplecze.wp_api_key and zaplecze.ssl_active:
            wp = WP_API(zaplecze.domain, zaplecze.wp_user, zaplecze.wp_api_key)
            zaplecze.wp_post_count = wp.get_post_count()
            zaplecze.wp_category_count = wp.get_category_count()
            zaplecze.save()


        return render(request, "partials/zaplecza_row.html", context={"i": zaplecze})
