from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.views.generic import View
import json


from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.setup_wp import Setup_WP
from datetime import datetime

class ZapleczeWrite(APIView):
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None

    def post(self, request, zaplecze_id):
        zaplecze = self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"res": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        categories, openai_key, a, p, links = \
                request.data.get('categories'), \
                str(request.data.get('openai_api_key')), \
                int(request.data.get('a_num')), \
                int(request.data.get('p_num')), \
                request.data.get('links')
        

        params = {
            "api_key" : openai_key,
            "domain_name" : data['domain'], 
            "wp_login" : data['wp_user'], 
            "wp_pass" : data['wp_api_key'],
            "lang" : data['lang']
        }

        if 'start_date' in request.data:
            params['start_date'] = datetime.strptime(request.data.get('start_date'), "%Y-%m-%d")
        if 'days_delta' in request.data:
            params['days_delta'] = int(request.data.get('days_delta'))
        if 'forward_delta' in request.data:
            params['forward_delta'] = True
        else:
            params['forward_delta'] = False
        
        o = OpenAI_article(**params)
        
        response = o.populate_structure(a, p, categories, "backend/src/CreateWPblog/", links)

        return Response(json.dumps(response), status=status.HTTP_201_CREATED)

class AnyZapleczeWrite(APIView):
    def post(self, request):
        categories, openai_key, a, p, links, domain, wp_user, lang = \
                request.data.get('categories'), \
                str(request.data.get('openai_api_key')), \
                int(request.data.get('a_num')), \
                int(request.data.get('p_num')), \
                request.data.get('links'), \
                request.data.get('domain'), \
                request.data.get('wp_user'), \
                request.date.get('lang')
        
        if 'wp_api_key' in request.data:
            wp_api_key = request.data.get('wp_api_key')
        elif 'wp_password': 
            s = Setup_WP(url=domain)
            s.login(login=wp_user, pwd=request.data.get('wp_password'))
            wp_api_key = s.get_api_key
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        params = {
            "api_key" : openai_key,
            "domain_name" : domain, 
            "wp_login" : wp_user, 
            "wp_pass" : wp_api_key,
            "lang" : lang
        }

        if 'start_date' in request.data:
            params['start_date'] = datetime.strptime(request.data.get('start_date'), "%Y-%m-%d")
        if 'days_delta' in request.data:
            params['days_delta'] = int(request.data.get('days_delta'))
        if 'forward_delta' in request.data:
            params['forward_delta'] = True
        else:
            params['forward_delta'] = False
        
        o = OpenAI_article(**params)
        
        response = o.populate_structure(a, p, categories, "backend/src/CreateWPblog/", links)

        return Response(json.dumps(response), status=status.HTTP_201_CREATED)
