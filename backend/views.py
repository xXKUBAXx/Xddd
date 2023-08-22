from django.shortcuts import render
from .models import Zaplecze
from .serializers import ZapleczeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.views.generic import View

from .src.CreateWPblog.create import Create
from .src.CreateWPblog.ftp import UploadFTP
from .src.CreateWPblog.setup_wp import Setup_WP
from .src.CreateWPblog.openai_article import OpenAI_article

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
    


    

class ZapleczeAPIDetail(APIView):
    
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None
        
    def get(self, request, zaplecze_id, *args, **kwargs):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with todo id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ZapleczeSerializer(zaplecze)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, zaplecze_id, *args, **kwargs):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with todo id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = {
            "domain": request.data.get("domain"),
            "url": request.data.get("url"),
            "login": request.data.get("login"),
            "password": request.data.get("password"),
            "db_user": request.data.get("db_user"),
            "db_pass": request.data.get("db_pass"),
            "ftp_user": request.data.get("ftp_user"),
            "ftp_pass": request.data.get("ftp_pass"),
            "wp_user": request.data.get("wp_user"),
            "wp_api_key": request.data.get("wp_api_key")
        }

        serializer = ZapleczeSerializer(instance = zaplecze, data=data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, zaplecze_id, *args, **kwargs):
        zaplecze = self.get_object(zaplecze_id)

        if not zaplecze:
            return Response(
                {"res": "Object with todo id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        zaplecze.delete()

        return Response(
            {"res": "Salto do śmieciary!"},
            status=status.HTTP_200_OK
        )
    

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
                {"res": "Object with todo id does not exists"},
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



class ZapleczeAPIStructure(APIView):
    
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None
        
    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)

        serializer = ZapleczeSerializer(zaplecze)

        data = serializer.data

        o = OpenAI_article(
            api_key=request.data.get("openai_api_key"),
            domain_name=data['domain'],
            wp_login=data['wp_user'],
            wp_pass=data['wp_api_key'],
            lang=data['lang']
        )

        structure = o.create_structure(data['topic'], request.data.get('cat_num'), request.data.get('subcat_num'))

        return Response(structure, status=status.HTTP_201_CREATED)




class Front(View):
    def get(self, request):
        queryset = Zaplecze.objects.values()
        context = {'queryset': queryset}
        return render(request, 'index.html', context)
    

class CreateZaplecze(View):
    def get(self, request):
        return render(request, 'create.html')
    

class ZapleczeUnit(View):
    def get(self, request, zaplecze_id):
        serializer = ZapleczeSerializer(Zaplecze.objects.get(id=zaplecze_id))
        
        context = {'data': serializer.data}

        return render(request, 'zaplecze.html', context)