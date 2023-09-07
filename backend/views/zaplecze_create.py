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

class ZapleczeAPICreate(APIView):

    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None

    def post(self, request, zaplecze_id, *args, **kwargs):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)

        data = serializer.data

        print(data['domain'])

        domain = data['domain']

        if not data['db_user']:
            create = Create(data)
            data['db_user'], data['db_pass'], data['ftp_user'], data['ftp_pass'] = create.do_stuff(domain)

            serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
            if serializer.is_valid():
                serializer.save()

            print("Connecting to FTP")
            f = UploadFTP(domain, data['ftp_user'], data['ftp_pass'], "backend/src/CreateWPblog/files")

            print("Initilazing WP setup")
        wp = Setup_WP(domain)

        if not data['wp_user'] == '':
            data['wp_user'], data['wp_password'] = wp.install(data['db_user'], data['db_pass'], domain.partition(".")[0])
            print("Tweaking WP options")
            wp.setup(data['wp_user'], data['wp_password'])
            serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
            if serializer.is_valid():
                serializer.save()

        if not data['wp_api_key'] == '':
            data['wp_api_key'] = wp.get_api_key(data['wp_user'], data['wp_password'])

        serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






