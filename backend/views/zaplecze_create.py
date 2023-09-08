from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.views.generic import View

from ..src.CreateWPblog.create import Create
from ..src.CreateWPblog.ftp import UploadFTP
from ..src.CreateWPblog.setup_wp import Setup_WP

'''
    1. Login to panel => register domain + change IP + SSL
    2. Setup DB
    3. Setup FTP
    4. Setup WP
    5. Change WP params
    6. Get WP API key
'''
class ZapleczeCreate(APIView):
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None

class ZapleczeCreateDomain(ZapleczeCreate):
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        domain = data['domain']
        if data['ftp_user']:
            return Response({"res": "This zaplecze alredy has FTP"}, status=status.HTTP_200_OK)
        create = Create(data)
        create.login()
        create.add_domain(domain)
        create.add_ip(domain)
        create.add_ssl()
        return Response(data, status=status.HTTP_200_OK)


class ZapleczeCreateDB(ZapleczeCreate):
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        domain = data['domain']
        if data['db_user']:
            return Response({"res": "This zaplecze alredy has DB"}, status=status.HTTP_200_OK)
        create = Create(data)
        create.login()
        data['db_user'], data['db_pass'] = create.add_db(domain)
        serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ZapleczeCreateFTP(ZapleczeCreate):
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        domain = data['domain']
        if data['ftp_user']:
            return Response({"res": "This zaplecze alredy has FTP"}, status=status.HTTP_200_OK)
        create = Create(data)
        create.login()
        data['ftp_user'], data['ftp_pass'] = create.add_ftp()
        serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
        if serializer.is_valid():
            serializer.save()
        UploadFTP(domain, data['ftp_user'], data['ftp_pass'], "backend/src/CreateWPblog/files")
        return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ZapleczeCreateSetupWP(ZapleczeCreate):
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        domain = data['domain']
        if data['wp_user'] and data['wp_user'] != "":
            return Response({"res": "This zaplecze alredy has WP"}, status=status.HTTP_200_OK)
        wp = Setup_WP(domain, data['email'], data['lang'])
        data['wp_user'], data['wp_password'] = wp.install(data['db_user'], data['db_pass'], domain.partition(".")[0])
        serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ZapleczeCreateTweakWP(ZapleczeCreate):
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        domain = data['domain']
        wp = Setup_WP(domain)
        wp.setup(data['wp_user'], data['wp_password'])
        return Response(data, status=status.HTTP_200_OK)

class ZapleczeCreateWPapi(ZapleczeCreate):
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        domain = data['domain']
        wp = Setup_WP(domain)
        if data['wp_api_key']:
            return Response({"res": "This zaplecze alredy has WP API key"}, status=status.HTTP_200_OK)
        
        data['wp_api_key'] = wp.get_api_key(data['wp_user'], data['wp_password'])
        serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






