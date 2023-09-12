from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.views.generic import View


from ..src.CreateWPblog.openai_article import OpenAI_article
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
        category, id, openai_key, a, p = \
                str(request.data.get('category')), \
                request.data.get('cat_id'), \
                str(request.data.get('openai_api_key')), \
                int(request.data.get('a_num')), \
                int(request.data.get('p_num'))
        

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
            params['forward_delta'] = bool(request.data.get('forward_delta'))
        
        o = OpenAI_article(**params)

        titles, cat_id = o.create_titles(category, a, id)
        print(category+" - created titles: \n - " + "\n - ".join(titles))

        urls = []
        for t in titles:
            urls.append(o.create_article(p, t, cat_id, True, "backend/src/CreateWPblog/"))

        return Response({"urls": urls, "id": id}, status=status.HTTP_201_CREATED)
    
