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

@method_decorator(csrf_exempt, name='dispatch')
class ZapleczeClassic(View):
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None

    def post(self, request, zaplecze_id):
        data = json.loads(request.body)
        zaplecze = self.get_object(zaplecze_id)


        graphicSource = data.get("graphicSource") #pixabay, unsplash, pexels
        # image_key = data.get("image_key") #openai, pixa, or unsplash
        image_key = "36043348-2f97c422170679f5ed532a796" #openai, pixa, or unsplash
        overlay_option = data.get("overlayOption") #wihOverlay, withoutOverlay
        date_input = data.get("dateInput") #2021-01-01
        publishInterval = data.get("publishInterval") #2
        openai.api_key = data.get("openai_api_key") #sk
        faq_option = data.get("faqOption") #withFaq, withoutFaq
        tsv_input = data.get("tsvInput")        
        
        # gathers data from tsv_input
        rows = tsv_input.strip().split("\n")
        headers = ["title", "graphic_theme", "graphic_theme2", "category", "length", "isfaq"]
        if all(header in rows[0] for header in headers):
            rows = rows[1:]
        category_array = []
        # print(settings.STATICFILES_DIRS[0])
        # makes texts, graphics, faqs and publish all to wp

        wp_api = WP_API(zaplecze.domain, zaplecze.wp_user, zaplecze.wp_api_key)
        date_controller = 0
        for row in rows:
            title, graphic_theme, graphic_theme2, category, length, isfaq = row.split("\t")
            article, opening = get_text(title, category, length, isfaq, language=zaplecze.lang)
            image_save_path = get_image(graphic_theme, title, overlay_option, graphicSource, image_key, graphic_theme2=None)
            publish_date = get_publish_date(date_input, publishInterval, date_controller)
            image_id = wp_api.upload_img(image_save_path)
            
            if '&' in category:
                categories = list(category.split('&'))
                for cat in categories:
                    category_array.append(wp_api.create_category(cat, generate_cat_desc(cat, language=zaplecze.lang)))
            else:
                category_array.append(wp_api.create_category(cat, generate_cat_desc(cat, language=zaplecze.lang)))

            category_array = [cat['id'] for cat in category_array]
            wp_api.post_article(title, article, opening, image_id, datetime.datetime.now(), category_array, author_id=1)
            date_controller += 1

            # publish_article(article, featured_image, publish_date, zaplecze.wp_user, zaplecze.wp_api_key)
            

        received_data = {
        "article": article,
        "publish_date": publish_date,
    }
        
        return JsonResponse({"message": "Dane zostały pomyślnie przetworzone!","received_data": received_data})


        # return JsonResponse({"message": "Dane zostały pomyślnie przetworzone!","received_data": received_data, "zaplecze_id": zaplecze.id})

    def get(self, request, *args, **kwargs):
        return JsonResponse({"error": "Nieprawidłowa metoda żądania."}, status=400)
    
    
    
def get_text(title, category, length, isfaq, language):
    headers = get_headers(title, language)
    print(headers)
    opening = get_opening(title, language)
    text = f'<h1>{title}</h1>\n{opening}'
    for header in headers:
        section = get_section(header, language)
        text += f'\n<h2>{header}</h2>\n{section}'
        print(text)
        print(f"\n\nobecna długość to {len(text)}\n\n")
        if len(text) > int(length):
            break

    if str(isfaq) == '1':
        faq = get_faq(title, language)
        text += f'\n{faq}'

    print(text)
    return text, opening


def get_headers(title, language):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe i bogate w informacje artykuły."},
            {"role": "user", "content": f'Stwórz 10 nagłówków h2 dla artykułu pod tytułem "{title}", zawrzyj je w tagach <h2>'}
            ]
        elif language.lower() == 'en':
            prompt = [
            {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
            {"role": "user", "content": f'Create 10 h2 headers for the article with the title "{title}", include them in <h2> tags.'}
            ]
        elif language.lower() == 'de':
            prompt = [
            {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
            {"role": "user", "content": f'Erstellen Sie 10 h2-Überschriften für den Artikel unter dem Titel "{title}", fügen Sie sie in <h2> ein'}
            ]
        elif language.lower() == 'cs':
            prompt = [
            {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
            {"role": "user", "content": f'Vytvořte nadpisy 10 h2 pro článek s názvem "{title}", zahrňte je do značek <h2>'}
            ]
        response = callBot(prompt, 300)

        content = response["choices"][0]["message"]["content"]


        header_list = re.findall(r'<h2>(.+?)</h2>', content)
        if not header_list:
            continue
        else:
            return header_list

def get_opening(title, language):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe i bogate w informacje artykuły."},
            {"role": "user", "content": f'Stwórz wstęp do artykułu pod tytułem "{title}", i zawrzyj go w tagach <p>'}
            ]
        elif language.lower() == 'en':
            prompt = [
            {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
            {"role": "user", "content": f'Create an introduction to the article with the title "{title}", and include it in the <p> tag.'}
            ]
        elif language.lower() == 'de':
            prompt = [
            {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
            {"role": "user", "content": f'Erstellen Sie eine Einleitung zum Artikel mit dem Titel "{title}" und fügen Sie ihn in das <p> Tag ein.'}
            ]
        elif language.lower() == 'cs':
            prompt = [
            {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
            {"role": "user", "content": f'Vytvořte úvod k článku s názvem "{title}" a vložte jej do tagu <p>.'}
            ]
        response = callBot(prompt, 600)

        content = response["choices"][0]["message"]["content"]


        opening_text = re.findall(r'<p>(.+?)</p>', content)
        if not opening_text:
            continue
        else:
            opening_text = "\n".join(opening_text)
            return opening_text
        
def get_section(header, language):
    while True:
            if language.lower() == 'pl':
                prompt = [
                {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe artykuły."},
                {"role": "user", "content": f'Napisz {random_pars(language)} paragrafy dla nagłówka {header} w języku polskim, każdy paragraf osadź pomiędzy tagami <p></p>.'}
                ]
            elif language.lower() == 'en':
                prompt = [
                {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
                {"role": "user", "content": f'Write {random_pars(language)} paragraphs for the header {header}, settle each paragraph between the <p></p> tags.'}
                ]
            elif language.lower() == 'de':
                prompt = [
                {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
                {"role": "user", "content": f'Schreiben Sie {random_pars(language)} Absätze für die Überschrift {header}, setzen Sie jeden Absatz zwischen die tags <p></p>.'}
                ]                                           
            elif language.lower() == 'cs':
                prompt = [
                {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
                {"role": "user", "content": f'Napište {random_pars(language)} odstavce pro nadpis {header} v češtině, každý odstavec vložte mezi značky <p></p>.'}
                ]                                           
            
            response = callBot(prompt, 600)
            content = response["choices"][0]["message"]["content"]
            content = re.sub(r'<br>', '', content)
            content = re.sub(r'\n\n+', '\n\n', content)
            content = content.replace("\n", " ")
            paragraphsList = re.findall(r'<p>(.+?)</p>', content)        
            paragraphs= ''
            
            for singlePar in paragraphsList:
                paragraphs += f'<p>{singlePar}</p>'

            return paragraphs

def get_faq(title, language):
    faq_questions = create_faq(title, language)
    for question in faq_questions:
        answer = ask_bot_faq(question, language)
        faq = f'\n<h2 class="faq-section">Najczęściej zadawane pytania (FAQ)</h2>\n<h3 class="faq-section">{question}</h3>\n<p>{answer}</p>'
    
    return faq

def create_faq(faq, language):
    search_query = faq
    search_url = f"https://www.google.com/search?q={search_query}&hl={language}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    related_questions = [tag['data-q'] for tag in soup.find_all(attrs={"data-q": True})]
    
    return related_questions

def ask_bot_faq(question, language):
        while True:
            if language.lower() == 'pl':
                prompt = [
                {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe artykuły."},
                {"role": "user", "content": f'Odpowiedz na pytanie "{question}" w maksymalnie 40 słowach. Odpowiedź umieść w jednym tagu <p></p>.'}
                ]
            elif language.lower() == 'en':
                prompt = [
                {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
                {"role": "user", "content": f'Answer the question "{question}" in up to 40 words. Place your answer in one <p></p> tag.'}
                ]
            elif language.lower() == 'de':
                prompt = [
                {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
                {"role": "user", "content": f'Beantworten Sie die Frage "{question}" in bis zu 40 Wörtern. Platzieren Sie Ihre Antwort in einem <p></p> Tag.'}
                ]
            elif language.lower() == 'cs':
                prompt = [
                {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
                {"role": "user", "content": f'Odpovězte prosím na "{question}" maximálně 40 slovy. Umístěte svou odpověď do jednoho tagu <p></p>.'}
                ]
            response = callBot(prompt, 300)

            answer = response["choices"][0]["message"]["content"]
            
            if not answer:
                continue
            else:
                return answer
        

def get_image(graphic_theme, title, overlay_option, graphicSource, image_key, graphic_theme2=None):
    if graphicSource == "pixabay":
        return get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2)
    elif graphicSource == "unsplash":
        # return get_unsplash_image(graphic_theme, graphic_theme2, overlay_option),
        return get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2) # temporary
    elif graphicSource == "ai":
        # return get_ai_image(graphic_theme, graphic_theme2, overlay_option)
        return get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2) # temporary


def get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2):
    
    keyword_list = [graphic_theme, graphic_theme2]

    for_loop_pixabay = 0
    image_url = None
    while True:
        if image_url:
            break
        for keyword in keyword_list:
            for_loop_pixabay += 1
            image_url = download_pixa_image(keyword, image_key)
            if image_url:
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content))
                image = image.resize((1200, 628)).convert('RGB')


                image_save_path = os.path.join(settings.STATICFILES_DIRS[0], "temp-image.webp")
                print(image_save_path)
                image.save(image_save_path, format='WEBP')
                
                return image_save_path
        if for_loop_pixabay >= 3:
            keyword_list = generate_emergency_keywords(title, graphic_theme, graphic_theme2)
        
    
    

def download_pixa_image(keyword, image_key):
    response = requests.get(f"https://pixabay.com/api/?key={image_key}&q={clean_keyword(keyword)}&image_type=photo")
    if response.status_code != 200:
        return None
    hits = response.json()["hits"]
    if not hits:
        return None
    while True:
        image_data = random.choice(hits)
        image_url = image_data["largeImageURL"]
        return image_url
    
def generate_emergency_keywords(title, graphic_theme, graphic_theme2):
    messages=[
                {
                    'role': 'system',
                    'content': 'Based on the title and two keywords, generate an English-language list of keywords that will be used to download graphics to Pixabay. Remember that keywords should be 1 or 2 words long and should be related to the title. Keywords divide ","',
                },
                {
                    'role': 'user',
                    'content': f'{title} | {graphic_theme} | {graphic_theme2}'
                }
            ],
            
    response = callBot(messages, 300)
    image_keywords = response["choices"][0]["message"]["content"]
    return image_keywords.split(",")

def clean_keyword(keyword):
    if keyword:
        return keyword.replace(" ", "+").lower()
    return None

# graphicSource = data.get("graphicSource") #pixabay, unsplash, pexels
# overlay_option = data.get("overlayOption") #wihOverlay, withoutOverlay

def get_time():
    current_time = datetime.datetime.now()
    random_time = current_time.replace(
        hour=random.randrange(24), 
        minute=random.randrange(60), 
        second=random.randrange(60),
        microsecond=0
    )
    return random_time.strftime('%H:%M:%S')

def get_publish_date(date_input, publishInterval, date_controller):
    date = datetime.datetime.strptime(date_input, "%Y-%m-%d")
    if date_controller != 0:
        date += datetime.datetime.timedelta(days=publishInterval * date_controller)
    return f'{date.date()}T{get_time()}'

def generate_cat_desc(cat, language):
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
            response = callBot(prompt, 300)

            description = response["choices"][0]["message"]["content"]
            
            if not description:
                continue
            else:
                return description


def callBot(prompt, price):
    while True:
        try:
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            max_tokens=price,
            n=1,
            stop=None,
            temperature=0.8,
            )
            return response

        except (openai.error.RateLimitError, openai.error.ServiceUnavailableError, openai.error.APIError) as e:
            print(f"Rate limit error: {e}")
            print('Funkcja odczeka 60 sekund i spróbuje ponownie')
            time.sleep(60)

def random_pars(language):
    random.randint(1, 3)

    switcher = {
        'pl':{1:'jeden', 2:'dwa', 3:'trzy'},
        'en':{1:'one', 2:'two', 3:'three'},
        'de':{1:'ein', 2:'zwei', 3:'drei'},
        'cs':{1:'jeden', 2:'dva', 3:'tři'}
    }

    return switcher[language][random.randint(1, 3)]