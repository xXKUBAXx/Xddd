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

from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.openai_api import OpenAI_API
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
        
        response, tokens, _ = o.populate_structure(a, p, categories, "backend/src/CreateWPblog/", links)

        try:
            account = get_object_or_404(Account, user_id=request.user.id)
            account.tokens_used += tokens
        except:
            account = Account.objects.create(user_id=request.user.id, tokens_used=tokens, openai_api_key=openai_key)
        account.save()
        

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
        
        response, tokens, _ = o.populate_structure(a, p, cats, "backend/src/CreateWPblog/", links, nofollow, topic)
        print({"data": response, "tokens": tokens})

        try:
            account = get_object_or_404(Account, user_id=request.user.id)
            account.tokens_used += tokens
        except:
            account = Account.objects.create(user_id=request.user.id, tokens_used=tokens, openai_api_key=openai_key)
        account.save()

        return Response({"data": response, "tokens": tokens}, status=status.HTTP_201_CREATED)


class ManyZapleczesWrite(APIView):
    serializer_class = WriteSerializer
    @swagger_auto_schema(
            operation_description="Write articles for multiple Zapleczas", 
            request_body=WriteSerializer, 
            responses={201:ResponseSerializer, 400:"Bad Request"}
            )
    
    def do_zaplecze(self, a, z, openai_key, lang, start_date, days_delta, forward_delta, p_num, topic):
        print(f"{len(a)} texts will be published on {z['domain']}")
        if topic == "":
            topic = a[0]["keyword"]
        params = {
                "api_key" : openai_key,
                "domain_name" : z["domain"], 
                "wp_login" : z["wp_user"], 
                "wp_pass" : z["wp_api_key"],
                "lang" : lang,
                "start_date": start_date, 
                "days_delta": days_delta,
                "forward_delta": forward_delta
            }
        
        if type(a)==dict:
            categories = 1
        else:
            categories = len(a)
        wp = WP_API(z["domain"], z["wp_user"], z["wp_api_key"])
        wp_cats = wp.get_categories()
        try:
            random.shuffle(wp_cats)
        except:
            print("Cannot shuffle")
            print(wp_cats)
            return {0: ["Wrong WordPress credentials"]}, 0, z["domain"]
        if len(wp_cats) >= categories:
            cats = wp_cats[:categories]
        else:
            cats = wp_cats
            for _ in range(categories - len(wp_cats)):
                cats.append({"id":1, "name": topic})

        o = OpenAI_article(**params)
        
        return o.populate_structure(1, p_num, cats, "backend/src/CreateWPblog/", a, 0, topic)
    

    async def add_tokens(self, id, toknes:int, openai_api_key:str = ""):
        try:
            account = await sync_to_async(get_object_or_404, thread_sensitive=False)(Account, user_id=id)
            account.tokens_used += toknes
        except:
            account = Account(
                user_id=id, 
                tokens_used=toknes, 
                openai_api_key=openai_api_key
                )
        await sync_to_async(account.save, thread_sensitive=False)()

    
    async def write_article(self, 
                            o:OpenAI_article, 
                            user,
                            title:str, 
                            header_num:int, 
                            cat_id:int = 1,
                            path:str = '',
                            links:list[dict] = None,
                            nofollow:int = 0,
                            ) -> tuple[str, int, int]:
        
        #add article to db
        l = Link(user=user.email, domain=o.get_domain(), link=links[0]['url'], keyword=links[0]['keyword'], done=False)
        await sync_to_async(l.save, thread_sensitive=False)()
                
        #generate headers & promt for generating image
        print("Creating headers for - ", title)
        headers, img_prompt, headers_tokens = await o.create_headers(title,header_num)
        await self.add_tokens(user.id, headers_tokens)
        
        p_tasks = []
        #write paragraphs with links first
        if links:
            for link, header in zip(links, headers[:len(links)]):
                p_tasks.append(asyncio.create_task(o.write_paragraph(title, header, link['keyword'], link['url'], nofollow)))
        #queue up rest of paragraphs
        for h in headers:
            p_tasks.append(asyncio.create_task(o.write_paragraph(title, h)))
        print("Writing paragraphs for article - ", title)
        paragraphs = await asyncio.gather(*p_tasks)
        #merge all texts into single string article
        text = ""
        for header, paragraph, tokens in paragraphs:
            await self.add_tokens(user.id, tokens)
            text += "<h2>"+header+"</h2>"
            text += paragraph

        #Write description
        desc, tokens = await o.write_description(text)
        await self.add_tokens(user.id, tokens)

        #Generate & download image
        if img_prompt != "":
            img = o.download_img(img_prompt, f"{path}files/test_photo{datetime.now().microsecond}.webp")
            #Upload image to WordPress
            img_id = o.upload_img(img)
            #Delete local image
            os.remove(img)
        else:
            print("No img prompt - TARAPATAS!!")
            img_id = None
        
        #Upload article to Wordpress
        if img_id:
            response = o.post_article(title, text, desc, img_id, o.publish_date['t'], cat_id)['link']
        else:
            print('no image id - uploading with default image')
            response = o.post_article(title, text, desc, "1", o.publish_date['t'], cat_id)['link']


        print("Uploaded article - ", response)
        o.shift_date()
        l.url = response
        l.done = True
        await sync_to_async(l.save, thread_sensitive=False)()
        return response
    
    
    
    async def main(self, 
                o:OpenAI_article,
                user,
                article_num:int, 
                header_num:int,
                categories:list[dict] = [],
                path:str = "",
                links:list[dict] = [],
                nofollow:int = 0, 
                topic:str = ""):
        
        '''
        GOTO data structure
        [
            {
                "cat": "",
                "articles": [
                    {
                        "title": "",
                        "headers": [], 
                        "paragraphs": [] 
                    }
                ], 
                ...articles
            },
            ...categories
        ]
        '''
        print("titles", article_num)
        titles_tasks = []
        # for category in categories:
        #     titles_tasks.append(asyncio.create_task(o.create_titles(category['name'],article_num,category['id'])))
        titles_tasks.append(asyncio.create_task(o.create_titles(topic,article_num,0)))

        titles_list = await asyncio.gather(*titles_tasks)

        articles_tasks = []
        for x, cat in zip(titles_list,categories):
            titles, _, tokens = x
            await self.add_tokens(user.id, tokens)
            for title, link in zip(titles,links):
                articles_tasks.append(asyncio.create_task(self.write_article(o, user, title, header_num, cat['id'], path, [link], nofollow)))
        res = await asyncio.gather(*articles_tasks)
        
        return res

    async def post(self, request):
        topic, lang, openai_key, p_num, start_date, days_delta, zapleczas, links = \
            request.data.get("topic"), \
            request.data.get("lang"), \
            request.data.get("openai_api_key"), \
            int(request.data.get("p_num")), \
            datetime.strptime(request.data.get('start_date'), "%Y-%m-%d"), \
            int(request.data.get("days_delta")), \
            json.loads(request.data.get("zapleczas")), \
            json.loads(request.data.get("links"))
        
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

        if 'forward_delta' in request.data:
            if request.data.get('forward_delta'):
                forward_delta = True
            else:
                forward_delta = False
        else:
            forward_delta = False
            
        start_dates = []
        tmp_date = start_date
        for a in articles:
            start_dates.append(tmp_date)
            tmp_date += timedelta(days=(days_delta * len(a) * (1 if forward_delta else -1)))

        
        tasks = []
        for a, z, sd in zip(articles, zapleczas, start_dates):
            #get categories from WP
            if type(a)==dict:
                categories = 1
            else:
                categories = len(a)
            wp = OpenAI_article(
                openai_key,
                z["domain"], 
                z["wp_user"], 
                z["wp_api_key"],
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
                return {0: ["Wrong WordPress credentials"]}, 0, z["domain"]
            if len(wp_cats) >= categories:
                cats = wp_cats[:categories]
            else:
                cats = wp_cats
                for _ in range(categories - len(wp_cats)):
                    cats.append({"id":1, "name": topic})


            tasks.append(
                asyncio.create_task(
                    self.main(
                        wp,
                        request.user,
                        len(a), 
                        p_num, 
                        cats, 
                        "backend/src/CreateWPblog/", 
                        a, 
                        0,
                        topic
                        )))
                
        res = await asyncio.gather(*tasks)
        print([x for r in res for x in r])
        return Response({"data": [x for r in res for x in r]}, status=status.HTTP_201_CREATED)
