from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from django.views.generic import View
import json
import random
from datetime import datetime


from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.setup_wp import Setup_WP
from ..src.CreateWPblog.wp_api import WP_API

class ZapleczeWrite(APIView):
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None

    serializer_class = WriteSerializer
    @swagger_auto_schema(
            operation_description="Write article for any Zaplecze", 
            request_body=WriteSerializer, 
            responses={201:ResponseSerializer, 400:"Bad Request"}
            )
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
        
        response, tokens = o.populate_structure(a, p, categories, "backend/src/CreateWPblog/", links)

        return Response({"data": response, "tokens": tokens}, status=status.HTTP_201_CREATED)

class AnyZapleczeWrite(APIView):
    serializer_class = WriteSerializer
    @swagger_auto_schema(
            operation_description="Write article for any Zaplecze", 
            request_body=WriteSerializer, 
            responses={201:ResponseSerializer, 400:"Bad Request"}
            )
    def post(self, request):
        categories, openai_key, a, p, links, domain, wp_user, lang = \
                request.data.get('categories'), \
                str(request.data.get('openai_api_key')), \
                int(request.data.get('a_num')), \
                int(request.data.get('p_num')), \
                request.data.get('links'), \
                request.data.get('domain'), \
                request.data.get('wp_user'), \
                request.data.get('lang')
        
        if 'wp_api_key' in request.data:
            wp_api_key = request.data.get('wp_api_key')
        elif 'wp_password': 
            s = Setup_WP(url=domain)
            wp_api_key = s.get_api_key(login=wp_user, pwd=request.data.get('wp_password'))
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        if 'nofollow' in request.data:
            nofollow = request.data.get('nofollow')
        else:
            nofollow = 0
        
        if 'topic' in request.data:
            topic = request.data.get('topic')

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
            if request.data.get('forward_delta'):
                params['forward_delta'] = True
            else:
                params['forward_delta'] = False
        else:
            params['forward_delta'] = False


        try:
            categories = int(categories)
            wp = WP_API(domain, wp_user, wp_api_key)
            wp_cats = wp.get_categories()
            random.shuffle(wp_cats)
            if len(wp_cats) >= categories:
                cats = wp_cats[:categories]
            else:
                cats = wp_cats
                for _ in range(categories - len(wp_cats)):
                    cats.append({"id":1, "name": topic})
        except:
            cats = categories
        
        
        o = OpenAI_article(**params)
        
        response, tokens = o.populate_structure(a, p, cats, "backend/src/CreateWPblog/", links, nofollow, topic)
        print({"data": response, "tokens": tokens})

        return Response({"data": response, "tokens": tokens}, status=status.HTTP_201_CREATED)


class ManyZapleczesWrite(APIView):
    serializer_class = WriteSerializer
    @swagger_auto_schema(
            operation_description="Write article for any Zaplecze", 
            request_body=WriteSerializer, 
            responses={201:ResponseSerializer, 400:"Bad Request"}
            )
    def post(self, request):
        topic, lang, openai_key, p_num, start_date, days_delta, zapleczas, links = \
            request.data.get("topic"), \
            request.data.get("lang"), \
            request.data.get("openai_api_key"), \
            int(request.data.get("p_num")), \
            datetime.strptime(request.data.get('start_date'), "%Y-%m-%d"), \
            int(request.data.get("days_delta")), \
            json.loads(request.data.get("zapleczas")), \
            json.loads(request.data.get("links"))
            
        
        
        articles = [links[i:i+len(zapleczas)] for i in range(0, len(links), len(zapleczas))]

        response, tokens = {}, 0

        for a, z in zip(articles, zapleczas):
            params = {
                "api_key" : openai_key,
                "domain_name" : z["domain"], 
                "wp_login" : z["wp_user"], 
                "wp_pass" : z["wp_api_key"],
                "lang" : lang,
                "start_date": start_date, 
                "days_delta": days_delta
            }
            if 'forward_delta' in request.data:
                if request.data.get('forward_delta'):
                    params['forward_delta'] = True
                else:
                    params['forward_delta'] = False
            else:
                params['forward_delta'] = False


            categories = len(a)
            wp = WP_API(z["domain"], z["wp_user"], z["wp_api_key"])
            wp_cats = wp.get_categories()
            random.shuffle(wp_cats)
            if len(wp_cats) >= categories:
                cats = wp_cats[:categories]
            else:
                cats = wp_cats
                for _ in range(categories - len(wp_cats)):
                    cats.append({"id":1, "name": topic})
        
        
            o = OpenAI_article(**params)
            
            res, t = o.populate_structure(1, p_num, cats, "backend/src/CreateWPblog/", links, 0, topic)
            response.update(res)
            tokens += t
            print({"data": res, "tokens": t})
            print({"data": response, "tokens": tokens})

        return Response({"data": response, "tokens": tokens}, status=status.HTTP_201_CREATED)
