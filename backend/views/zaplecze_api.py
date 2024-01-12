import asyncio
import os
from datetime import datetime

from ..models import Account, Link
from ..src.CreateWPblog.openai_article import OpenAI_article
from django.shortcuts import get_object_or_404

from adrf.views import APIView
from asgiref.sync import sync_to_async
import logging


class ZAPIView(APIView):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
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
        return toknes


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
                
        #generate headers & promt for generating image
        # print("Creating headers for - ", title)
        headers, img_prompt, headers_tokens = await o.create_headers(title,header_num)
        total_tokens += await self.add_tokens(user.id, headers_tokens)
        
        p_tasks = []
        #write paragraphs with links first
        if links:
            for link, header in zip(links, headers[:len(links)]):
                p_tasks.append(asyncio.create_task(o.write_paragraph(title, header, link['keyword'], link['url'], nofollow)))
        #queue up rest of paragraphs
        for h in headers:
            p_tasks.append(asyncio.create_task(o.write_paragraph(title, h)))
        # print("Writing paragraphs for article - ", title)
        paragraphs = await asyncio.gather(*p_tasks)
        #merge all texts into single string article
        text = ""
        for header, paragraph, tokens in paragraphs:
            total_tokens += await self.add_tokens(user.id, tokens)
            text += "<h2>"+header+"</h2>"
            text += paragraph

        #Write description
        desc, tokens = await o.write_description(text)
        total_tokens += await self.add_tokens(user.id, tokens)
        

        #Generate & download image
        if img_prompt != "":
            img = await o.download_img(img_prompt, f"{path}files/test_photo{datetime.now().microsecond}.webp")
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


        #shift date of publication for next article
        o.shift_date()
        # print("Uploaded article - ", response)

        #Update database with article url and mark as done
        l.url = response
        l.done = True
        await sync_to_async(l.save, thread_sensitive=False)()
        return response, total_tokens
    
    
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
                articles_tasks.append(
                    asyncio.create_task(
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
                            )))
        res = await asyncio.gather(*articles_tasks)
        
        return res