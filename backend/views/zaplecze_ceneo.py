from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ..models import Zaplecze
import json
import csv
from io import StringIO
import openai
import time
import datetime
import random
import re
from bs4 import BeautifulSoup
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from ..src.CreateWPblog.wp_api import WP_API
import asyncio
from asgiref.sync import sync_to_async
import aiohttp


from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.openai_api import OpenAI_API
import pandas as pd

from openai import OpenAI
from rest_framework import status
from django.http import JsonResponse


@method_decorator(csrf_exempt, name='dispatch')
class ZapleczeCeneo(View):
    async def get_object(self, zaplecze_id):
        try:
            return await sync_to_async(Zaplecze.objects.get, thread_sensitive=False)(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None
        

    async def post(self, request, zaplecze_id):
        data = json.loads(request.body)
        zaplecze = await self.get_object(zaplecze_id)

        if not zaplecze:
            return
        
        user_id, user_mail = await sync_to_async(check_user)(request)

        # ceneoCat = data.get('compSelect')  # mouse / keyboard
        # ceneoQuant = int(data.get('compQuant'))  # ilość porównań
        # graphicSource = data.get('graphicSource')  # pixabay, pexels, ai
        # pixabay_api_key = "36043348-2f97c422170679f5ed532a796" #openai, pixa, or unsplash
        # pexels_api_key = "K4INRjrCzmznTXPESmWi4PyvmoV9VRqj9c9RKq1huu5ouhb4BO23RfFS"
        # overlay_option = data.get('overlayOption')  # withOverlay, withoutOverlay
        # date_input = data.get('dateInput')  # 2021-01-01
        # publishInterval = data.get('publishInterval')  # 2
        # openai_api_key = data.get('openai_api_key')  # sk
        # overlay_color = data.get('overlayColor')
            

        ceneoQuant = 5
        pixabay_api_key = "36043348-2f97c422170679f5ed532a796"
        publishInterval = 2
        overlay_color = '204, 255, 102'
        openai_api_key = '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'
        date_input = '2021-01-01'

        # overlay_option = 'withOverlay'
        # graphicSource = 'ceneo'

       

        rgb_fill_preset = overlay_color.split(",")
        rgb_fill_preset = [int(channel) for channel in rgb_fill_preset]

        wp_api = WP_API(zaplecze.domain, zaplecze.wp_user, zaplecze.wp_api_key)
        
        # local server
        filename = '../wesele_1_striped.csv' 

        prod_list = await get_ceneo_by_quant(filename, ceneoQuant)

        global date_controller
        date_controller = []
        
        for i in range(ceneoQuant):
            date_controller.append(i+1)

        zaplecze_lang = zaplecze.lang

        print(f'{user_mail} ordered {ceneoQuant} posts - Ceneo')

        await process_product_list(prod_list, user_id, openai_api_key, zaplecze_lang, wp_api, date_input, publishInterval, pixabay_api_key, date_controller)


        received_data = {
        "article": 'comp_text',
        "publish_date": 'publish_date',
    }
        
        return JsonResponse({"message": "Dane zostały pomyślnie przetworzone!","received_data": received_data})


        # return JsonResponse({"message": "Dane zostały pomyślnie przetworzone!","received_data": received_data, "zaplecze_id": zaplecze.id})

    async def get(self, request, *args, **kwargs):
        return JsonResponse({"error": "Nieprawidłowa metoda żądania."}, status=400)

def check_user(request):
    user = request.user
    if user.is_authenticated:
        return user.id, user.email
    else:
        return None
        
async def process_product_list(prod_list, user_id, openai_api_key, zaplecze_lang, wp_api, date_input, publishInterval, pixabay_api_key, date_controller):
            async with aiohttp.ClientSession() as session:
                tasks = [process_product(session, product, user_id, openai_api_key, zaplecze_lang, wp_api, date_input, publishInterval, pixabay_api_key, date_controller) for product in prod_list]
                await asyncio.gather(*tasks)

async def process_product(session, product, user_id, openai_api_key, zaplecze_lang, wp_api, date_input, publishInterval, pixabay_api_key, date_controller):

    address = product[0]
    title = product[1]
    product_original_text = product[6]
    product_graphic = product[4]
    
    opening = await get_opening(session, title, openai_api_key, zaplecze_lang)
    category = await get_category(session, title, openai_api_key, zaplecze_lang)
    product_new_text = await get_new_product_text(session, product_original_text, openai_api_key, zaplecze_lang)
    
    done_text = f'<div class="product data"><p class="product-price">Cena: <strong>{product[3]}</strong></p><p class="product-categories">Kategoria: <strong>{product[8]}</strong></p><p class="product-creator">Producent: <strong>{product[7]}</strong></p><span style="display:none;" class="product-url">{address}</span></div><div class="original-text">' + product_original_text + '</div>' + ' <br><br> ' + '<div class="product-text">' + product_new_text + '</div>'

    image_save_path = await download_and_save_image(session, product_graphic, user_id, title, category, pixabay_api_key)
    publish_date = await get_publish_date(date_input, publishInterval, date_controller)
    image_id = wp_api.upload_img(image_save_path)

    categories = [await sync_to_async(wp_api.create_category, thread_sensitive=False)(cat, await generate_cat_desc(session, cat, openai_api_key, zaplecze_lang)) for cat in (category.split('&') if '&' in category else [category])]
    categories = categories[0]['id']

    response = wp_api.post_article(title, done_text, opening, image_id, publish_date, categories, author_id=1)
    

    if os.path.isfile(image_save_path):
        os.remove(image_save_path)
        print(f'Image {image_save_path} has been deleted')

async def download_and_save_image(session, image_url, user_id, title, fallback_keyword, pixabay_api_key):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
    except (requests.RequestException, IOError):

        print(f"Error downloading image from {image_url}. Falling back to Pixabay with keyword: {fallback_keyword}")
        image_url = download_pixabay_image(fallback_keyword, pixabay_api_key)
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

    image = image.convert('RGB')
    image_save_path = os.path.join(settings.STATICFILES_DIRS[0], f"temp-image-{user_id}-{create_unique_title(title)}.webp")
    image.save(image_save_path, format='WEBP')
    return image_save_path

async def get_category(session, title, openai_api_key, language):
     while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Na podstawie nazwy produktu odpowiedz 1 nazwą kategorii i niczym więcej:"},
            {"role": "user", "content": f'{title}'}
            ]

        response = await callBot(prompt, 100, openai_api_key)

        category = response["choices"][0]["message"]["content"]

        if not category:
            continue
        else:
            return category

def create_unique_title(title):
    title = title.replace(" ", "").lower()
    title = re.sub(r'[^a-zA-Z0-9]', '', title)
    return title

async def download_pixabay_image(keyword, api_key):
    url = f"https://pixabay.com/api/?key={api_key}&q={keyword.replace(' ', '+')}&image_type=photo&per_page=3"
    try:
        response = requests.get(url)
        data = response.json()
        if data['hits']:
            return data['hits'][0]['largeImageURL']
    except requests.RequestException:
        print("Error downloading image from Pixabay.")
        return None

async def get_ceneo_by_quant(filename, ceneoQuant):
    chosen_rows = []

    with open(filename, encoding="utf8") as f:
        reader = csv.reader(f)
        csv_listed = list(reader)
        for _ in range(int(ceneoQuant)):
            chosen_rows.append(random.choice(csv_listed))

    return chosen_rows

        
async def get_new_product_text(session, original_text, openai_api_key, language):

    while True:
            if language.lower() == 'pl':
                prompt = [
                {"role": "system", "content": "Prowadzisz sklep internetowy. Napisz opis produktu na podstawie przekazanych informacji. Opis powinien być w formie lekko-umiarkowano konwersacyjnej, ale powinien zachować powagę sklepu internetowego. Pamiętaj, że opis tekstu powinien być dłuższy niż 300 słów. Dodaj nagłówki H2 do tekstu. Tekst umieść w tagach html <p> i <h2>."},
                {"role": "user", "content": f'Opis, na podstawie którego napiszesz nowy opis produktu: {original_text}'}
                ]
            # elif language.lower() == 'en':
            #     prompt = [
            #     {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
            #     {"role": "user", "content": f'Write {random_pars(language)} paragraphs for the header {header}, settle each paragraph between the <p></p> tags.'}
            #     ]
            # elif language.lower() == 'de':
            #     prompt = [
            #     {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
            #     {"role": "user", "content": f'Schreiben Sie {random_pars(language)} Absätze für die Überschrift {header}, setzen Sie jeden Absatz zwischen die tags <p></p>.'}
            #     ]                                           
            # elif language.lower() == 'cs':
            #     prompt = [
            #     {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
            #     {"role": "user", "content": f'Napište {random_pars(language)} odstavce pro nadpis {header} v češtině, každý odstavec vložte mezi značky <p></p>.'}
            #     ]                                           
            
            response = await callBot(prompt, 4096, openai_api_key)
            content = response["choices"][0]["message"]["content"]
            text = re.findall(r'<.*>', content, re.DOTALL)
            html_content = text[0]
            html_content = re.sub(r'\n\n+', '\n\n', html_content)
            html_content = html_content.replace("\n", " ")

            return html_content

async def get_opening(session, article_title, openai_api_key, language):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Jesteś specjalistą SEO i redaktorem w sklepie internetowym."},
            {"role": "user", "content": f'Stwórz wstęp do artykułu który porównuje produkty, pod tytułem "{article_title}", i zawrzyj go w tagach <p>. Wstęp powinien być długi na 500 liter.'}
            ]
        elif language.lower() == 'en':
            prompt = [
            {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
            {"role": "user", "content": f'Create an introduction to the article with the title "{comp_title}", and include it in the <p> tag. The introduction should be 500 letters long.'}
            ]
        elif language.lower() == 'de':
            prompt = [
            {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
            {"role": "user", "content": f'Erstellen Sie eine Einleitung zum Artikel mit dem Titel "{comp_title}" und fügen Sie ihn in das <p> Tag ein. Die Einleitung sollte 500 Buchstaben lang sein.'}
            ]
        elif language.lower() == 'cs':
            prompt = [
            {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
            {"role": "user", "content": f'Vytvořte úvod k článku s názvem "{comp_title}" a vložte jej do tagu <p>. Úvod by měl mít 500 písmen.'}
            ]
        response = await callBot(prompt, 1000, openai_api_key)

        content = response["choices"][0]["message"]["content"]


        opening_text = re.findall(r'<p>(.+?)</p>', content)
        if not opening_text:
            continue
        else:
            opening_text = "\n".join(opening_text)
            return opening_text
        

def callBigBot(prompt, price, openai_api_key):
    # print(openai_api_key)
    # input("Tutaj się wypierdala, albo tutaj")
    client = OpenAI(api_key=openai_api_key)
    while True:
        try:
            response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=prompt,
            max_tokens=price,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            temperature=0.8,
            )
            response = json.loads(response.json())
            return response

        except openai.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
        except Exception as e:
            print("Unknown error, waiting & resuming - ", e)
            time.sleep(3)
            continue
        break
            


def get_time():
    current_time = datetime.datetime.now()
    random_time = current_time.replace(
        hour=random.randrange(24), 
        minute=random.randrange(60), 
        second=random.randrange(60),
        microsecond=0
    )
    return random_time.strftime('%H:%M:%S')

async def get_publish_date(date_input, publishInterval, date_controller):
    date = datetime.datetime.strptime(date_input, "%Y-%m-%d")
    if int(date_controller[0]) != 0:
        date += datetime.timedelta(days=int(publishInterval) * int(date_controller.pop(0)))

    new_date = f'{date.date()}T{get_time()}'
    return datetime.datetime.strptime(new_date, "%Y-%m-%dT%H:%M:%S")

async def generate_cat_desc(session, cat, openai_api_key, language):
    while True:
            if language.lower() == 'pl':
                prompt = [
                {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe artykuły."},
                {"role": "user", "content": f'Napisz opis do kategorii bloga, która nazywa się {cat}.'}
                ]
            elif language.lower() == 'en':
                prompt = [
                {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
                {"role": "user", "content": f'Write a description for the blog category called {cat}.'}
                ]
            elif language.lower() == 'de':
                prompt = [
                {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
                {"role": "user", "content": f'Schreiben Sie eine Beschreibung für die Blog-Kategorie namens {cat}.'}
                ]
            elif language.lower() == 'cs':
                prompt = [
                {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
                {"role": "user", "content": f'Napište popis pro kategorii blogu s názvem {cat}.'}
                ]
            response = await callBot(prompt, 300, openai_api_key)
    
            description = response["choices"][0]["message"]["content"]

            if not description:
                continue
            else:
                return description


async def callBot(prompt, price, openai_api_key):

    client = OpenAI(api_key=openai_api_key)
    while True:
        try:
            response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=prompt,
            max_tokens=price,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            temperature=0.8,
            )
            response = json.loads(response.json())
            return response

        except openai.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
        except Exception as e:
            print("Unknown error, waiting & resuming - ", e)
            time.sleep(3)
            continue
        break



