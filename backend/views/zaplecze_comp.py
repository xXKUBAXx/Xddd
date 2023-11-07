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
        openai.api_key = data.get('openai_api_key')  # sk
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

        filename = '../mouses.csv' if compSelect == 'mouse' else '../keyboards.csv' if compSelect == 'keyboard' else None
        
        list_of_pairs, pairs_titles = get_pairs(filename, compQuant)        

        if compSelect == 'mouse':
            graphic_theme = "computer mouse"
            graphic_theme2 = "computer"
            category = "Myszki komputerowe&Porównania myszek"
            length = 4000
        elif compSelect == 'keyboard':
            graphic_theme = "computer keyboard"
            graphic_theme2 = "computer"
            category = "Klawiatury komputerowe&Porównania klawiatur"
            length = 4000

        
        # main function starts here4

        for pair in list_of_pairs:
            title = pairs_titles[list_of_pairs.index(pair)]
            article, opening = get_comp_text(title, category, pair, length, faq_option, language=zaplecze.lang)


        # print(settings.STATICFILES_DIRS[0])
        # makes texts, graphics, faqs and publish all to wp

        
        date_controller = 0
        
       
        category_array = []

        new_title, text, opening = get_text(title, textData, category, length, isfaq, language=zaplecze.lang)
        image_save_path = get_image(graphic_theme, title, overlay_option, graphicSource, image_key, graphic_theme2)
        publish_date = get_publish_date(date_input, publishInterval, date_controller)
        image_id = wp_api.upload_img(image_save_path)
        
        if '&' in category:
            categories = list(category.split('&'))
            for cat in categories:
                category_array.append(wp_api.create_category(cat, generate_cat_desc(cat, language=zaplecze.lang)))
        else:
            category_array.append(wp_api.create_category(cat, generate_cat_desc(cat, language=zaplecze.lang)))

        category_array = [cat['id'] for cat in category_array]
        wp_api.post_article(new_title, text, opening, image_id, datetime.datetime.now(), category_array, author_id=1)
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
    

def get_comp_text(title, category, pair, length, faq_option, language):
    print(f'Generating comparison of: {title}')
    comp_title, headers = get_comp_skeleton(title, language)
    opening = get_opening(comp_title, language)
    text = f'{opening}'
    for header in headers:
        section = get_comp_section(comp_title, pair, language, header)
        text += f'\n<h2>{header}</h2>\n{section}'
        if len(text) > int(length):
            break

    if str(faq_option) == 'withFaq':
        faq = get_faq(title, language)
        text += f'\n{faq}'

    return comp_title, text, opening

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


def get_comparison(title, pair, language):
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
        response = callBigBot(prompt, 10000)

        content = response["choices"][0]["message"]["content"]

        prompt = [
        {"role": "system", "content": "Jesteś wnikliwym redaktorem strony technologicznej, który zajmuje się pisaniem porównań elektroniki i wyciąganiem wniosków, dzięki czemu konsumenci mogą podejmować lepsze decyzje zakupowe."},
        {"role": "user", "content": f'Rozwiń tekst, który otrzymasz. Rozwiń treść w taki sposób, aby stworzyć długi na 6000 znaków artykuł, dodaj śródtytuły w <h2>. Całość zapisz w tagach html (<h1>, <h2>, <p>). Tekst: {content}. Zoptymalizuj też tabelkę, dodaj pierwszą kolumnę do tagów <th>.'}
        ]

        response = callBigBot(prompt, 10000)

        content = response["choices"][0]["message"]["content"]

        if len(content) >= 4000:
            return content


def get_comp_skeleton(title, language):
    while True:
        if language.lower() == 'pl':
            prompt = [
            {"role": "system", "content": "Jesteś wnikliwym redaktorem strony informacyjnej, który pisze ciekawe i bogate w informacje artykuły."},
            {"role": "user", "content": f'Stwórz nagłówki na podstawie produktów, o których będzie artykuł-porównanie - "{title}" i zawrzyj je w tagach <h1> i <h2>'}
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


        comp_title = re.findall(r'<h1>(.*?)</h1>', content, re.DOTALL)
        headers = re.findall(r'<h2>(.*?)</h2>', content, re.DOTALL)

        if not comp_title or not headers:
            continue
        else:
            comp_title = comp_title[0] if comp_title else ""
            return comp_title, headers
        
def get_opening(comp_title, language):
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
        response = callBot(prompt, 600)

        content = response["choices"][0]["message"]["content"]


        opening_text = re.findall(r'<p>(.+?)</p>', content)
        if not opening_text:
            continue
        else:
            opening_text = "\n".join(opening_text)
            return opening_text
        
def get_comp_section(comp_title, pair, language, header):
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
            
            response = callBigBot(prompt, 5000)
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
    faq = f'\n<h2 class="faq-section">Najczęściej zadawane pytania (FAQ)</h2>'
    for question in faq_questions:
        answer = ask_bot_faq(question, language)
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
            
def callBigBot(prompt, price):
    while True:
        try:
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
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
        

def get_image(graphic_theme, title, overlay_option, graphicSource, image_key, graphic_theme2=None):
    if graphicSource == "pixabay":
        return get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2)
    elif graphicSource == "unsplash":
        # return get_unsplash_image(graphic_theme, graphic_theme2, overlay_option),
        return get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2) # temporary
    elif graphicSource == "ai":
        # return get_ai_image(graphic_theme, graphic_theme2, overlay_option)
        return get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2) # temporary


def get_pixabay_image(graphic_theme, title, overlay_option, image_key, graphic_theme2=None):
    
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
                    return addOverlay(image_save_path, title)
                else:
                    return image_save_path
        if for_loop_pixabay >= 3:
            keyword_list = generate_emergency_keywords(title, graphic_theme, graphic_theme2)
        
    
def addOverlay(save_path, title, overlay_fill_preset=[168, 150, 50, 92]):
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
    
def generate_emergency_keywords(title, graphic_theme, graphic_theme2=None):
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
        date += datetime.timedelta(days=int(publishInterval) * int(date_controller))
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