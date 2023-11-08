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



from ..src.CreateWPblog.openai_article import OpenAI_article
from ..src.CreateWPblog.openai_api import OpenAI_API
import pandas as pd

from openai import OpenAI


@method_decorator(csrf_exempt, name='dispatch')
class ZapleczeComp(View):
    def get_object(self, zaplecze_id):
        try:
            return Zaplecze.objects.get(id=zaplecze_id)
        except Zaplecze.DoesNotExist:
            return None

    def post(self, request, zaplecze_id):
        data = json.loads(request.body)
        zaplecze = self.get_object(zaplecze_id)

        compSelect = data.get('compSelect')  # mouse / keyboard
        compQuant = int(data.get('compQuant'))  # ilość porównań
        graphicSource = data.get('graphicSource')  # pixabay, pexels, ai
        pixabay_api_key = "36043348-2f97c422170679f5ed532a796" #openai, pixa, or unsplash
        pexels_api_key = "K4INRjrCzmznTXPESmWi4PyvmoV9VRqj9c9RKq1huu5ouhb4BO23RfFS"
        overlay_option = data.get('overlayOption')  # withOverlay, withoutOverlay
        date_input = data.get('dateInput')  # 2021-01-01
        publishInterval = data.get('publishInterval')  # 2
        openai_api_key = data.get('openai_api_key')  # sk
        faq_option = data.get('faqOption')  # withFaq, withoutFaq
        overlay_color = data.get('overlayColor')

        rgb_fill_preset = overlay_color.split(",")
        rgb_fill_preset = [int(channel) for channel in rgb_fill_preset]

        if graphicSource is not None:
            if graphicSource == "pixabay":
                image_key = pixabay_api_key
                emergency_key = pexels_api_key
            elif graphicSource == "pexels":
                image_key = pexels_api_key
                emergency_key = pixabay_api_key
            else:
                image_key = None
                emergency_key = None

        wp_api = WP_API(zaplecze.domain, zaplecze.wp_user, zaplecze.wp_api_key)

        filename = '../../mouses.csv' if compSelect == 'mouse' else '../../keyboards.csv' if compSelect == 'keyboard' else None
        
        list_of_pairs, pairs_titles = get_pairs(filename, compQuant)        

        if compSelect == 'mouse':
            graphic_theme = "computer mouse"
            graphic_theme2 = "computer"
            category = "Myszki komputerowe&Porównania myszek"
            compItem = "myszek komputerowych"
            length = 6000
        elif compSelect == 'keyboard':
            graphic_theme = "computer keyboard"
            graphic_theme2 = "computer"
            category = "Klawiatury komputerowe&Porównania klawiatur"
            compItem = "klawiatur komputerowych"
            length = 6000

        date_controller = 0
        # main function starts here4

        for pair in list_of_pairs:
            category_array = []
            title = pairs_titles[list_of_pairs.index(pair)]
            comp_title, comp_text, opening = get_comp_text(title, compItem, openai_api_key, pair, length, faq_option, language=zaplecze.lang)
            image_save_path = get_image(graphic_theme, comp_title, openai_api_key, overlay_option, rgb_fill_preset, graphicSource, zaplecze.lang, graphic_theme2, image_key, emergency_key)
            publish_date = get_publish_date(date_input, publishInterval, date_controller)
            image_id = wp_api.upload_img(image_save_path)
            if '&' in category:
                categories = list(category.split('&'))
                for cat in categories:
                    category_array.append(wp_api.create_category(cat, generate_cat_desc(cat, openai_api_key, language=zaplecze.lang)))
            else:
                category_array.append(wp_api.create_category(category, generate_cat_desc(category,openai_api_key, language=zaplecze.lang)))

            category_array = [cat['id'] for cat in category_array]
            wp_api.post_article(comp_title, comp_text, opening, image_id, publish_date, category_array, author_id=1)
            date_controller += 1
            if os.path.isfile(image_save_path):
                os.remove(image_save_path)
                print(f'Image {image_save_path} has been deleted')

         

            # publish_article(article, featured_image, publish_date, zaplecze.wp_user, zaplecze.wp_api_key)
            

        received_data = {
        "article": comp_text,
        "publish_date": publish_date,
    }
        
        return JsonResponse({"message": "Dane zostały pomyślnie przetworzone!","received_data": received_data})


        # return JsonResponse({"message": "Dane zostały pomyślnie przetworzone!","received_data": received_data, "zaplecze_id": zaplecze.id})

    def get(self, request, *args, **kwargs):
        return JsonResponse({"error": "Nieprawidłowa metoda żądania."}, status=400)

def get_pairs(filename, compQuant):
    list_of_pairs = []
    pairs_titles = []

    if filename is not None:
        df = pd.read_csv(filename, converters={'compared_with': eval})
    
        pairs = extract_pairs(df, compQuant)

        if not pairs:
            print("Nie można znaleźć żadnych par spełniających kryteria.")
            return
        else:
            # uncomment for production
            # df.to_csv(filename, index=False)
            
            exclude_keys = ['id', 'in_use', 'compared_with']
            
            for pair in pairs:
                
                column_titles = [key for key in pair['row1'].keys() if key not in exclude_keys]
        
                product_string = ','.join(column_titles) + '\n'
                
                product_string += ','.join(str(pair['row1'][key]) if key in pair['row1'] else '' for key in column_titles) + '\n'
                
                product_string += ','.join(str(pair['row2'][key]) if key in pair['row2'] else '' for key in column_titles)

                product_names = [pair['row1']['name'], pair['row2']['name']]

                pairs_titles.append(product_names)
                list_of_pairs.append(product_string)
                
                product_string = ''
                product_names = ''
    
    return list_of_pairs, pairs_titles

def extract_pairs(df, quantity):
    pairs = []
    attempts = 0
    
    while len(pairs) < quantity and attempts < 100 * quantity:
        attempts += 1


        available_products = df[df['in_use'] == 0]
        

        if len(available_products) < 2:
            break


        sample = available_products.sample(2)
        if sample.empty:
            continue
        
        row1, row2 = sample.iloc[0].to_dict(), sample.iloc[1].to_dict()
        

        if row2['id'] not in row1['compared_with'] and row1['id'] not in row2['compared_with']:

            if abs(row1['price'] - row2['price']) <= 100:

                df.at[sample.index[0], 'compared_with'].append(row2['id'])
                df.at[sample.index[1], 'compared_with'].append(row1['id'])

                df.at[sample.index[0], 'in_use'] += 1
                df.at[sample.index[1], 'in_use'] += 1


                pairs.append({'pair_id': (row1['id'], row2['id']), 'row1': row1, 'row2': row2})
            else:

                continue
    
    return pairs
    

def get_comp_text(title, compItem, openai_api_key, pair, length, faq_option, language):
    print(f'Generating comparison of: {title}')
    comp_title, headers = get_comp_skeleton(title, compItem, language, openai_api_key)
  
    opening = get_opening(comp_title, language, openai_api_key)
    text = f'{opening}'
    comp_table = get_comp_table(comp_title, pair, language, openai_api_key)
    text = f'<h2>Specyfikacja produktów</h2>\n{comp_table}'
    print("Nie zjebało się")
    for header in headers:
        print(f"Nie zjebało się - leci {header}")
        section = get_comp_section(comp_title, pair, language, header, openai_api_key)
        text += f'\n<h2>{header}</h2>\n{section}'
        if len(text) > int(length):
            break

    if str(faq_option) == 'withFaq':
        faq = get_faq(title, language, openai_api_key)
        text += f'\n{faq}'

    return comp_title, text, opening

def get_comp_table(comp_title, pair, language, openai_api_key):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": f"Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe artykuły porównujące produkty. W swojej pracy wykorzystaj następujące informacje o produktach: {pair}"},
            {"role": "user", "content": f'Stwórz tabelkę htmlową na podstawie znanych Ci danych, do artykułu {comp_title}. Nazwa produktów powinna wystąpić tylko raz. Tabelka powinna być pionowa, osadzona w tagu <div class="comp-table">. Jeżeli jakaś wartość jest oznaczona "nie dotyczy", nie dodawaj jej do tabelki. Nie dodawaj do tabelki: linku, url, ocen, opinii.'}
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
        response = callBot(prompt, 1000, openai_api_key)

        content = response["choices"][0]["message"]["content"]

        comp_table_match = re.search(r'(<div class="comp-table">.*?</div>)', content, re.DOTALL)

        if comp_table_match:
            comp_table_content = comp_table_match.group(1)
            return comp_table_content


        

def get_section(header, language, openai_api_key):
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
            
            response = callBot(prompt, 600, openai_api_key)
            content = response["choices"][0]["message"]["content"]
            content = re.sub(r'<br>', '', content)
            content = re.sub(r'\n\n+', '\n\n', content)
            content = content.replace("\n", " ")
            paragraphsList = re.findall(r'<p>(.+?)</p>', content)        
            paragraphs= ''
            
            for singlePar in paragraphsList:
                paragraphs += f'<p>{singlePar}</p>'

            return paragraphs


def get_comparison(title, pair, language, openai_api_key):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Jesteś wnikliwym redaktorem strony technologicznej, który zajmuje się pisaniem porównań elektroniki i wyciąganiem wniosków, dzięki czemu konsumenci mogą podejmować lepsze decyzje zakupowe."},
            {"role": "user", "content": f'Na podstawie następujących danych: {textData}, napisz tytuł (zamieść go w h1) i artykuł-porównanie produktów. Tekst zamieść w tagach html (<h1>, <h2>, <p>). W treści zamieść także tabelkę html, którą stworzysz na podstawie danych o produktach.'}
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
        response = callBigBot(prompt, 10000, openai_api_key)

        content = response["choices"][0]["message"]["content"]

        prompt = [
        {"role": "system", "content": "Jesteś wnikliwym redaktorem strony technologicznej, który zajmuje się pisaniem porównań elektroniki i wyciąganiem wniosków, dzięki czemu konsumenci mogą podejmować lepsze decyzje zakupowe."},
        {"role": "user", "content": f'Rozwiń tekst, który otrzymasz. Rozwiń treść w taki sposób, aby stworzyć długi na 6000 znaków artykuł, dodaj śródtytuły w <h2>. Całość zapisz w tagach html (<h1>, <h2>, <p>). Tekst: {content}. Zoptymalizuj też tabelkę, dodaj pierwszą kolumnę do tagów <th>.'}
        ]

        response = callBigBot(prompt, 10000, openai_api_key)

        content = response["choices"][0]["message"]["content"]

        if len(content) >= 4000:
            return content


def get_comp_skeleton(title, compItem, language, openai_api_key):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe i bogate w informacje artykuły."},
            {"role": "user", "content": f'Stwórz 5 nagłówków do artykułu-porównania {compItem} - "{title}" i zawrzyj je w tagach <h1> i <h2>.Nagłówek <h1> musi zawierać nazwy porównywanych produktów. Nagłówki <h2> powinny być zawierać nazwy produktów w dowolnej formie.'}
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
        response = callBot(prompt, 600, openai_api_key)

        content = response["choices"][0]["message"]["content"]


        comp_title = re.findall(r'<h1>(.*?)</h1>', content, re.DOTALL)
        headers = re.findall(r'<h2>(.*?)</h2>', content, re.DOTALL)

        if not comp_title or not headers:
            continue
        else:
            comp_title = comp_title[0] if comp_title else ""
            return comp_title, headers
        
def get_opening(comp_title, language, openai_api_key):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe i bogate w informacje artykuły."},
            {"role": "user", "content": f'Stwórz wstęp do artykułu który porównuje produkty, pod tytułem "{comp_title}", i zawrzyj go w tagach <p>'}
            ]
        elif language.lower() == 'en':
            prompt = [
            {"role": "system", "content": "You are an insightful editor of a news site who writes interesting articles."},
            {"role": "user", "content": f'Create an introduction to the article with the title "{comp_title}", and include it in the <p> tag.'}
            ]
        elif language.lower() == 'de':
            prompt = [
            {"role": "system", "content": "Sie sind ein einfühlsamer Redakteur einer Nachrichtenseite, der interessante Artikel schreibt."},
            {"role": "user", "content": f'Erstellen Sie eine Einleitung zum Artikel mit dem Titel "{comp_title}" und fügen Sie ihn in das <p> Tag ein.'}
            ]
        elif language.lower() == 'cs':
            prompt = [
            {"role": "system", "content": "Jste bystrý redaktor zpravodajského webu, který píše zajímavé články."},
            {"role": "user", "content": f'Vytvořte úvod k článku s názvem "{comp_title}" a vložte jej do tagu <p>.'}
            ]
        response = callBot(prompt, 600, openai_api_key)

        content = response["choices"][0]["message"]["content"]


        opening_text = re.findall(r'<p>(.+?)</p>', content)
        if not opening_text:
            continue
        else:
            opening_text = "\n".join(opening_text)
            return opening_text
        
def get_comp_section(comp_title, pair, language, header, openai_api_key):
    while True:
            if language.lower() == 'pl':
                prompt = [
                {"role": "system", "content": f"Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe artykuły porównujące produkty. W swojej pracy wykorzystaj następujące informacje o produktach: {pair}"},
                {"role": "user", "content": f'Napisz {random_pars(language)} paragrafy dla nagłówka {header}, który zostanie zamieszczony w artykule pod tytułem {comp_title}, każdy paragraf osadź pomiędzy tagami <p></p>.'}
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
            
            response = callBigBot(prompt, 5000, openai_api_key)
            content = response["choices"][0]["message"]["content"]
            content = re.sub(r'<br>', '', content)
            content = re.sub(r'\n\n+', '\n\n', content)
            content = content.replace("\n", " ")
            paragraphsList = re.findall(r'<p>(.+?)</p>', content)        
            paragraphs= ''
            
            for singlePar in paragraphsList:
                paragraphs += f'<p>{singlePar}</p>'

            return paragraphs

def get_faq(title, language, openai_api_key):
    faq_questions = create_faq(title, language)
    faq = f'\n<h2 class="faq-section">Najczęściej zadawane pytania (FAQ)</h2>'
    for question in faq_questions:
        answer = ask_bot_faq(question, language, openai_api_key)
        faq += f'\n<h3 class="faq-section">{question}</h3>\n<p>{answer}</p>'
    
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

def ask_bot_faq(question, language, openai_api_key):
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
            response = callBot(prompt, 300, openai_api_key)

            answer = response["choices"][0]["message"]["content"]
            
            if not answer:
                continue
            else:
                return answer
            
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
            
def get_image(graphic_theme, title, openai_api_key, overlay_option, rgb_fill_preset, graphicSource, language, graphic_theme2=None, image_key=None, emergency_key=None):
    if graphicSource == "pixabay":
        return get_pixabay_image(graphic_theme, title, openai_api_key, overlay_option, rgb_fill_preset, image_key, graphic_theme2)
    elif graphicSource == "pexels":
        return get_pexels_image(graphic_theme, title, openai_api_key, overlay_option, rgb_fill_preset, image_key, emergency_key, graphic_theme2)
    elif graphicSource == "ai":
        return  get_ai_image(graphic_theme, title, openai_api_key, language, overlay_option, rgb_fill_preset,)
    
def get_ai_image(graphic_theme, title, ai_key, language, overlay_option, rgb_fill_preset):
    openai_api = OpenAI_API(ai_key, language)
    image_url = openai_api.create_img(f'Generate feature image for article about {title}')
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    image = image.resize((1200, 628)).convert('RGB')

    image_save_path = os.path.join(settings.STATICFILES_DIRS[0], "temp-image.webp")
    print(image_save_path)
    image.save(image_save_path, format='WEBP')
    
    if overlay_option == "withOverlay":
        return addOverlay(image_save_path, title, rgb_fill_preset)
    else:
        return image_save_path
    
def get_pexels_image(graphic_theme, title, openai_api_key, overlay_option, rgb_fill_preset, pexels_api_key, emergency_key, graphic_theme2=None):
    
    keyword_list = [graphic_theme, graphic_theme2]

    for_loop_pexels = 0
    image_url = None
    while True:
        if image_url:
            break
        for keyword in keyword_list:
            if not keyword:  # Skip if keyword is None
                continue
            for_loop_pexels += 1
            image_url = download_pexels_image(keyword, pexels_api_key)
            
            if image_url:
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content))
                image = image.resize((1200, 628)).convert('RGB')

                image_save_path = os.path.join(settings.STATICFILES_DIRS[0], "temp-image.webp")
                print(image_save_path)
                image.save(image_save_path, format='WEBP')
                
                if overlay_option == "withOverlay":
                    return addOverlay(image_save_path, title, rgb_fill_preset)
                else:
                    return image_save_path
        if for_loop_pexels >= 3:
            keyword_list = generate_emergency_keywords(title, openai_api_key, graphic_theme, graphic_theme2)

        if not image_url:
            break

def download_pexels_image(keyword, openai_api_key, pexels_api_key, emergency_key):
    headers = {
        'Authorization': pexels_api_key
    }

    rate_limit_check_response = requests.head("https://api.pexels.com/v1/search", headers=headers)
    if 'X-Ratelimit-Remaining' in rate_limit_check_response.headers:
        rate_limit_remaining = int(rate_limit_check_response.headers['X-Ratelimit-Remaining'])
        if rate_limit_remaining <= 0:
            print("Rate limit exceeded.")
            return get_pixabay_image(keyword, openai_api_key, emergency_key)
        
        else:
            response = requests.get(f"https://api.pexels.com/v1/search?query={clean_keyword(keyword)}&per_page=1", headers=headers)
            if response.status_code == 200:
                results = response.json()
                if results['photos']:
                    first_result = results['photos'][0]
                    return first_result['src']['original']


def get_pixabay_image(graphic_theme, title, openai_api_key, overlay_option, rgb_fill_preset, image_key, graphic_theme2=None):
    
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
                
                if overlay_option == "withOverlay":
                    return addOverlay(image_save_path, title, rgb_fill_preset)
                else:
                    return image_save_path
        if for_loop_pixabay >= 3:
            keyword_list = generate_emergency_keywords(title, openai_api_key, graphic_theme, graphic_theme2)

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
    
def addOverlay(save_path, title, overlay_fill_preset=[168, 150, 50, 90]):

    if len(overlay_fill_preset) == 3:
        overlay_fill_preset.append(90)

    pure_image = Image.open(save_path).convert('RGBA')
    
    overlay_height = pure_image.size[1] // 2
    overlay = Image.new('RGBA', pure_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([(0, pure_image.size[1] - overlay_height), (pure_image.size[0], pure_image.size[1])], fill=tuple(overlay_fill_preset))

    image_with_overlay = Image.alpha_composite(pure_image, overlay)

    draw = ImageDraw.Draw(image_with_overlay)
    text = title

    if len(text) <= 60:
        font = ImageFont.truetype(f"{settings.STATICFILES_DIRS[0]}/Montserrat-Bold.ttf", 60)
    elif 60 < len(text) <= 95:
        font = ImageFont.truetype(f"{settings.STATICFILES_DIRS[0]}/Montserrat-Bold.ttf", 50)
    else:
        font = ImageFont.truetype(f"{settings.STATICFILES_DIRS[0]}/Montserrat-Bold.ttf", 40)

    max_width = int(image_with_overlay.width * 0.9)
    lines = wrap_text(text, font, max_width)

    y_start = (image_with_overlay.height // 2) + 20
    line_spacing = 10  

    num_lines = len(lines)
    if num_lines == 3:
        start_drawing_height = 360
        line_spacing = 15
    else:
        start_drawing_height = 400
        line_spacing = 20

    total_text_height = num_lines * (font.getbbox(lines[0])[3] - font.getbbox(lines[0])[1]) + (num_lines - 1) * line_spacing

    if total_text_height > overlay_height:
        start_drawing_height -= total_text_height - overlay_height

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (image_with_overlay.width - text_width) // 2
        y = (pure_image.height // 2) + 20 + i * (text_height + line_spacing)
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    image_with_overlay.convert('RGB').save(save_path, format='WEBP')
    
    return save_path

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        text_bbox = font.getbbox(" ".join(current_line))
        width = text_bbox[2] - text_bbox[0]
        if width > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]

    lines.append(" ".join(current_line))
    return lines

def download_pexels_image(keyword, openai_api_key, pexels_api_key, emergency_key):
    headers = {
        'Authorization': pexels_api_key
    }

    rate_limit_check_response = requests.head("https://api.pexels.com/v1/search", headers=headers)
    if 'X-Ratelimit-Remaining' in rate_limit_check_response.headers:
        rate_limit_remaining = int(rate_limit_check_response.headers['X-Ratelimit-Remaining'])
        if rate_limit_remaining <= 0:
            print("Rate limit exceeded.")
            return get_pixabay_image(keyword, openai_api_key, emergency_key)
        
        else:
            response = requests.get(f"https://api.pexels.com/v1/search?query={clean_keyword(keyword)}&per_page=1", headers=headers)
            if response.status_code == 200:
                results = response.json()
                if results['photos']:
                    first_result = results['photos'][0]
                    return first_result['src']['original']
    
def generate_emergency_keywords(title, openai_api_key, graphic_theme, graphic_theme2=None):
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
            
    response = callBot(messages, 300, openai_api_key)
    image_keywords = response["choices"][0]["message"]["content"]
    return image_keywords.split(",")

def clean_keyword(keyword):
    if keyword:
        return keyword.replace(" ", "+").lower()
    return None


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
        date += datetime.timedelta(days=int(publishInterval) * int(date_controller))

    new_date = f'{date.date()}T{get_time()}'
    return datetime.datetime.strptime(new_date, "%Y-%m-%dT%H:%M:%S")

def generate_cat_desc(cat, openai_api_key, language):
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
            response = callBot(prompt, 300, openai_api_key)
    
            description = response["choices"][0]["message"]["content"]

            if not description:
                continue
            else:
                return description


def callBot(prompt, price, openai_api_key):
    # print(openai_api_key)
    # input("Tutaj się wypierdala")
    client = OpenAI(api_key=openai_api_key)
    while True:
        try:
            response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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

def random_pars(language):
    random.randint(1, 3)

    switcher = {
        'pl':{1:'jeden', 2:'dwa', 3:'trzy'},
        'en':{1:'one', 2:'two', 3:'three'},
        'de':{1:'ein', 2:'zwei', 3:'drei'},
        'cs':{1:'jeden', 2:'dva', 3:'tři'}
    }

    return switcher[language][random.randint(1, 3)]