import asyncio
import os
from datetime import datetime

from ..models import Account, Link
from ..src.CreateWPblog.openai_article import OpenAI_article
from django.shortcuts import get_object_or_404

from adrf.views import APIView
from asgiref.sync import sync_to_async
import logging
from django.conf import settings



class ZAPIView(APIView):

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def add_tokens(self, id, toknes:int, cost:float, openai_api_key:str = ""):
        try:
            try:
                account = await sync_to_async(get_object_or_404, thread_sensitive=False)(Account, user_id=id)
                account.tokens_used += toknes
                account.USD += cost
                print(f"added {toknes} tokens and {cost} USD to account")
            except:
                account = Account(
                    user_id=id, 
                    tokens_used=toknes, 
                    USD=cost,
                    openai_api_key=openai_api_key
                    )
            await sync_to_async(account.save, thread_sensitive=False)()
            return toknes
        except:
            return 0


    async def write_article(self, 
                            o:OpenAI_article, 
                            user,
                            task_id,
                            title:str, 
                            header_num:int, 
                            ul_id:str = "",
                            cat_id:int = 1,
                            path:str = '',
                            links:list[dict] = None,
                            nofollow:int = 0,
                            ) -> tuple[str, int, int]:
        
        #add article to db
        if not settings.DEBUG:
            l = Link(
                user=user.email, 
                task_id=task_id,
                ul_id=ul_id,
                domain=o.get_domain(), 
                link=links[0]['url'], 
                keyword=links[0]['keyword'], 
                done=False
                )
            await sync_to_async(l.save, thread_sensitive=False)()

        total_tokens = 0
        total_cost = 0
                
        #generate headers & promt for generating image
        if settings.DEBUG:
            print("Creating headers for - ", title)
        headers, img_prompt, headers_tokens, cost = await o.create_headers(title,header_num)
        total_tokens += await self.add_tokens(user.id, headers_tokens, cost)
        total_cost += cost
        
        p_tasks = []
        #write paragraphs with links first
        if links:
            for link, header in zip(links, headers[:len(links)]):
                p_tasks.append(asyncio.create_task(o.write_paragraph(title, header, link['keyword'], link['url'], nofollow)))
        #queue up rest of paragraphs
        for h in headers:
            p_tasks.append(asyncio.create_task(o.write_paragraph(title, h)))
        if settings.DEBUG:
            print("Writing paragraphs for article - ", title)
        paragraphs = await asyncio.gather(*p_tasks)
        #merge all texts into single string article
        text = ""
        for header, paragraph, tokens, cost in paragraphs:
            total_tokens += await self.add_tokens(user.id, tokens, cost)
            total_cost += cost
            text += "<h2>"+header+"</h2>"
            text += paragraph

        #Write description
        desc, tokens, cost = await o.write_description(text)
        total_tokens += await self.add_tokens(user.id, tokens, cost)
        total_cost += cost
        

        #Generate & download image
        if img_prompt != "":
            img, cost = await o.download_img(img_prompt, f"{path}files/test_photo{datetime.now().microsecond}.webp")
            #Upload image to WordPress
            img_id = o.upload_img(img)
            #Delete local image
            os.remove(img)
        else:
            print("No img prompt - generating image from title!!")
            img, cost = await self.download_img(
                f"Create image for article titled - {title}", 
                f"{path}files/test_photo{datetime.now().microsecond}.webp")
            #Upload image to WordPress
            img_id = self.upload_img(img)
            #Delete local image
            os.remove(img)
        total_cost += cost
        
        #Upload article to Wordpress
        if img_id:
            response = o.post_article(title, text, desc, img_id, o.publish_date['t'], cat_id)['link']
        else:
            print('no image id - uploading with default image')
            response = o.post_article(title, text, desc, "1", o.publish_date['t'], cat_id)['link']


        #shift date of publication for next article
        o.shift_date()
        if settings.DEBUG:
            print("Uploaded article - ", response)

        if not settings.DEBUG:
            #Update database with article url and mark as done
            l.url = response
            l.done = True
            await sync_to_async(l.save, thread_sensitive=False)()
        return response, total_tokens, total_cost
    
    
    async def write_task(self, 
                o:OpenAI_article,
                user,
                task_id,
                ul_id,
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
        # for category in categories:
        #     titles_tasks.append(asyncio.create_task(o.create_titles(category['name'],article_num,category['id'])))
        titles_list = await o.create_titles(topic,article_num,0)


        articles_tasks = set()
        for x, cat in zip([titles_list],categories):
            titles, _, tokens, cost = x
            await self.add_tokens(user.id, tokens, cost)
            for title, link in zip(titles,links):
                articles_task = asyncio.create_task(
                        self.write_article(
                            o=o, 
                            user=user, 
                            task_id=task_id, 
                            title=title, 
                            header_num=header_num, 
                            ul_id=ul_id, 
                            cat_id=cat['id'], 
                            path=path, 
                            links=[link], 
                            nofollow=nofollow
                            ))
                articles_tasks.add(articles_task)
                articles_task.add_done_callback(articles_tasks.discard)
        res = await asyncio.gather(*articles_tasks)
        
        return res