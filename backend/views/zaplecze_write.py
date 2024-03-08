from django.shortcuts import get_object_or_404
from ..models import Zaplecze, Account, Link
from ..serializers import *
from adrf.views import APIView
from asgiref.sync import sync_to_async
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
import json
import random
from datetime import datetime, timedelta
import asyncio
import os
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from threading import Thread

from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.openai_api import OpenAI_API
from ..src.CreateWPblog.setup_wp import Setup_WP
from ..src.CreateWPblog.wp_api import WP_API
from .zaplecze_api import ZAPIView
from .utils import log_user
from ..throttling import WriteZapleczaThrottle


class ZapleczeWrite(ZAPIView):
    throttle_classes = [WriteZapleczaThrottle]
    async def get_object(self, zaplecze_id):
        try:
            return await sync_to_async(Zaplecze.objects.get, thread_sensitive=False)(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None

    serializer_class = WriteSerializer
    @swagger_auto_schema(
            operation_description="Write article for any Zaplecze", 
            request_body=WriteSerializer, 
            responses={201:ResponseSerializer, 400:"Bad Request"}
            )
    async def post(self, request, zaplecze_id):
        # throttle = WriteZapleczaThrottle()
        # throttle.get_history(request)
        # throttle.add_timestamp()
        if ( len(json.loads(request.data.get('categories')))*int(request.data.get('a_num')) > 50 ):
            self.logger.info(f"{request.user.email} - Cannot write {len(json.loads(request.data.get('categories')))*int(request.data.get('a_num'))} categories - limit surpassed!")
            return Response(
                {"data": "Maximum article noumber exceeded. Please submit at most 30 articles at once"},
                status=status.HTTP_400_BAD_REQUEST
            )
        zaplecze = await self.get_object(zaplecze_id)
        if not zaplecze:
            return Response(
                {"data": "Object with this id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ZapleczeSerializer(zaplecze)
        data = serializer.data
        categories, openai_key, a, p = \
                json.loads(request.data.get('categories')), \
                str(request.data.get('openai_api_key')), \
                int(request.data.get('a_num')), \
                int(request.data.get('p_num'))
        
        try:
            links = json.loads(request.data.get('links'))
        except: 
            links = []
        
        self.logger.info(f"{request.user.email} - Writing {len(categories)*a} articles at {data['domain']}")        

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
        
        try:
            response = await o.main(a, p, categories, "backend/src/CreateWPblog/", links)
        except Exception as e:
            return Response({"data": str(e)}, status=status.HTTP_408_REQUEST_TIMEOUT)

        total_tokens = 0
        total_cost = 0
        result = {}
        for url, cat_id, t, c in response:
            total_tokens += t
            total_cost += c
            if cat_id in result.keys():
                result[cat_id].append(url)
            else:
                result[cat_id] = [url]
                
        await self.add_tokens(request.user.id, total_tokens, total_cost, openai_key)
        
        self.logger.info(f"{request.user.email} - Done writing {len(categories)*a} articles at {data['domain']}")        
        return Response({"data": result, "tokens": total_tokens, "cost": total_cost}, status=status.HTTP_201_CREATED)
    

class AnyZapleczeWrite(APIView):
    serializer_class = WriteSerializer
    @swagger_auto_schema(
            operation_description="Write article for any Zaplecze", 
            request_body=WriteSerializer, 
            responses={201:ResponseSerializer, 400:"Bad Request"}
            )
    async def post(self, request):
        categories, openai_key, a, p, links, domain, wp_user, lang = \
                request.data.get('categories'), \
                str(request.data.get('openai_api_key')), \
                int(request.data.get('a_num')), \
                int(request.data.get('p_num')), \
                request.data.get('links'), \
                request.data.get('domain'), \
                request.data.get('wp_user'), \
                request.data.get('lang')
        
        self.logger.info(f"{request.user.email} - Writing {len(categories)*a} articles at {domain}")        
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
        
        response, tokens, _ = o.populate_structure(a, p, cats, "backend/src/CreateWPblog/", links, nofollow, topic)
        print({"data": response, "tokens": tokens})

        try:
            account = get_object_or_404(Account, user_id=request.user.id)
            account.tokens_used += tokens
        except:
            account = Account.objects.create(user_id=request.user.id, tokens_used=tokens, openai_api_key=openai_key)
        account.save()

        self.logger.info(f"{request.user.email} - Done writing {len(categories)*a} articles at {domain}")        
        return Response({"data": response, "tokens": tokens}, status=status.HTTP_201_CREATED)


class ManyZapleczesWrite(ZAPIView):
    serializer_class = WriteSerializer
    @swagger_auto_schema(
            operation_description="Write articles for multiple Zapleczas", 
            request_body=WriteSerializer, 
            responses={201:ResponseSerializer, 400:"Bad Request"}
            )
    

    async def select_wp_cats(self, article_links, zaplecze:dict, openai_key:str, topic:str, lang:str, sd:datetime, days_delta:int, forward_delta:bool):
        categories = 1 if type(article_links)==dict else len(article_links)

        wp = OpenAI_article(
            openai_key,
            zaplecze["domain"], 
            zaplecze["wp_user"], 
            zaplecze["wp_api_key"],
            lang,
            sd,
            days_delta,
            forward_delta
            )
        wp_cats = wp.get_categories()
        try:
            random.shuffle(wp_cats)
        except:
            print("Cannot shuffle")
            print(wp_cats)
            return wp, None
        if len(wp_cats) >= categories:
            cats = wp_cats[:categories]
        else:
            cats = wp_cats
            for _ in range(categories - len(wp_cats)):
                cats.append({"id":1, "name": topic})
        
        return wp, cats
    
    

    async def post(self, request):
        #get data from request body
        topic = request.data.get("topic")
        lang = request.data.get("lang")
        openai_key = request.data.get("openai_api_key")
        p_num = int(request.data.get("p_num"))
        start_date = datetime.strptime(request.data.get('start_date'), "%Y-%m-%d")
        days_delta = int(request.data.get("days_delta"))
        if type(request.data.get("zapleczas")) == str:
            zapleczas = json.loads(request.data.get("zapleczas"))
        else:
            zapleczas = request.data.get("zapleczas")
        if type(request.data.get("links")) == str:
            links = json.loads(request.data.get("links"))
        else:
            links = request.data.get("links")

        
        try:
            self.logger.info(f"{request.user.email} - Writing {len(links)} links")        
        except:
            self.logger.info(f"Anonym - Writing {len(links)} links")        
        if 'forward_delta' in request.data:
            forward_delta = True if request.data.get('forward_delta') else False
        else:
            forward_delta = False


        #distribute links across articles (1 link per article)
        random.shuffle(links)
        articles = [[] for _ in zapleczas]
        if len(links) == len(zapleczas):
            articles = [[l] for l in links]
        else:
            while len(links)>0:
                for i in range(len(zapleczas)):
                    try:
                        articles[i].append(links.pop())
                    except IndexError:
                        break

            
        #calculate start dates for each articles group
        start_dates = []
        tmp_date = start_date
        for a in articles:
            start_dates.append(tmp_date)
            tmp_date += timedelta(days=(days_delta * len(a) * (1 if forward_delta else -1)))


        
        #get new task ID
        task_id = await sync_to_async(Link.objects.order_by, thread_sensitive=False)('task_id')
        task_id = await sync_to_async(task_id.last, thread_sensitive=False)()
        try:
            task_id = task_id.task_id + 1
        except AttributeError:
            task_id = 1
        
        tasks = []
        for article_links, zaplecze, sd in zip(articles, zapleczas, start_dates):
            try:
                wp, cats = await self.select_wp_cats(article_links, zaplecze, openai_key, topic, lang, sd, days_delta, forward_delta)
            except Exception as e:
                print(e)
                continue

            if cats == None:
                print(f"Wrong credentials to {zaplecze['domain']} - {zaplecze['wp_user']}:{zaplecze['wp_api_key']}")
                continue
                
            
            tasks.append(
                asyncio.create_task(
                    self.write_task(
                        wp,
                        request.user,
                        task_id,
                        request.data.get("ul_id"),
                        len(article_links), 
                        p_num, 
                        cats, 
                        "backend/src/CreateWPblog/", 
                        article_links, 
                        0,
                        topic if len(topic) > 3 else article_links[0]['keyword']
                        )))
                
        
        channel_layer = get_channel_layer()
        group_name = 'user-notifications'
        event = {
            "type": "notification",
            "text": f"Ukończono zlecenie nr {task_id}", 
            "url": "/user",
            "email": request.user.id
        }
        
        # loop = asyncio.new_event_loop()
        # t = Thread(target=self.start_background_loop, args=(loop,), daemon=True)
        # t.start()

        # res = asyncio.run_coroutine_threadsafe(self.write_all_articles(tasks), loop)

        try:
            res = await asyncio.gather(*tasks)
        except Exception as e:
            return Response({"data": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        # loop.stop()
        # print([x for r in res for x in r])
        await channel_layer.group_send(group_name, event)
        
        try:
            self.logger.info(f"{request.user.email} - Done writing {len(json.loads(request.data.get('links')))} links")        
        except:
            self.logger.info(f"Anonym - Done writing links")        
        return Response({"data": [x for r in res for x, _, _ in r], "tokens": sum([t for r in res for _, t, _ in r]), "cost": sum([c for r in res for _, _, c in r])}, status=status.HTTP_201_CREATED)
