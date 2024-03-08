from django.shortcuts import render, get_object_or_404
from ..models import Zaplecze, Account, Link, Banner, ZapleczeCategory
from ..serializers import ZapleczeSerializer, AccountSerializer
from rest_framework.views import APIView
from django.views.generic import View, edit
from django.utils.decorators import method_decorator
from django.db.models.functions import Length
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from ..src.CreateWPblog.openai_api import OpenAI_API
from backend.forms import RegisterZapleczeForm, AddZapleczeCategory
from django.shortcuts import redirect
from django.core.mail import send_mail


import json
import urllib
from .utils import log_user


@method_decorator(log_user(), name='dispatch')
class Front(View):
    def get(self, request):
        queryset = Zaplecze.objects.values()

        try:
            data = SocialAccount.objects.get(user=request.user).extra_data
        except:
            data = {}

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        context = {
            'queryset': queryset[::-1],
            'social_data': data,
            'papaj_spi': papaj_spi
        }

        return render(request, 'index.html', context)
        

@method_decorator(log_user(), name='dispatch')
class ZapleczaTable(View):
    def get(self, request):
        return render(request, "zaplecza.html", {"queryset": Zaplecze.objects.order_by("-id").values()})
    
@method_decorator(log_user(), name='dispatch')
class CreateZaplecze(View):
    def get(self, request):
        try:
            data = SocialAccount.objects.get(user=request.user).extra_data
        except:
            data = {}

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        langs = OpenAI_API("").get_langs()
        context = {'social_data': data, 'langs': langs, 'papaj_spi': papaj_spi}


        return render(request, 'create.html', context)


@method_decorator(log_user(), name='dispatch')
class RegisterZapleczeFormView(edit.FormView):
    def get(self, request):
        form = RegisterZapleczeForm()
        context = {"form": form}
        return render(request, "register.html", context)

    def post(self, request):
        form = RegisterZapleczeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")
            

    
@method_decorator(log_user(), name='dispatch')
class UpdateZaplecze(View):        
    def get(self, request, zaplecze_id):
        if zaplecze_id:
            serializer = ZapleczeSerializer(Zaplecze.objects.get(id=zaplecze_id))
        else:
            serializer.data = {}
        try:
            data = SocialAccount.objects.get(user=request.user).extra_data
        except:
            data = {}

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        context = {'social_data': data, 'data': serializer.data, 'papaj_spi': papaj_spi}
        return render(request, 'update.html', context)
    
@method_decorator(log_user(), name='dispatch')
class ZapleczeUnit(View):
    def get(self, request, zaplecze_id):
        serializer = ZapleczeSerializer(Zaplecze.objects.get(id=zaplecze_id))
        
        context = {'data': serializer.data}

        category_form = AddZapleczeCategory()

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        context = {
            'data': serializer.data,
            'papaj_spi': papaj_spi,
            'category_form': category_form
        }

        return render(request, 'zaplecze.html', context)

    def post(self, request, zaplecze_id):
        zaplecze = Zaplecze.objects.get(id=zaplecze_id)
        category_form = AddZapleczeCategory(request.POST, instance=zaplecze)
        if category_form.is_valid():
            category_form.save()
            return redirect(f'/{zaplecze_id}')

    

@method_decorator(log_user(), name='dispatch')
class WriteLink(View):
    def detect_change(self, val1, val2):
        if val1 > val2:
            return 1
        elif val1 == val2:
            return 0
        else:
            return -1
        
    def get(self, request, umowa_id):
        with urllib.request.urlopen(f"https://panel.verseo.pl/get_client_eichner_subpages.php?token=ewwg37sht579wqegwhedki4r5i98we34ytwue5uj&id_umowy={umowa_id}") as url:
            umowa = json.load(url)['data'][0]
        
        parsed_umowa = []
        for row in umowa['frazy']:
            row['data_wczoraj'] = row['data wczoraj']
            try:
                row['pozycja_wczoraj'] = int(row['pozycja wczoraj'])
            except:
                row['pozycja_wczoraj'] = 0
            row['data_dzisiaj'] = row['data dzisiaj']
            try:
                row['pozycja_dzisiaj'] = int(row['pozycja dzisiaj'])
            except: 
                row['pozycja_dzisiaj'] = 0
            del row['data wczoraj']
            del row['pozycja wczoraj']
            del row['data dzisiaj']
            del row['pozycja dzisiaj']
            parsed_umowa.append(row)
        
        umowa['frazy'] = parsed_umowa

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        categories = ZapleczeCategory.objects.all()
        category_data = []
        for category in categories:
            num_zaplecze = category.zaplecze_set.count()
            category_data.append({'category': category, 'id':category.id, 'num_zaplecze': num_zaplecze})

        zaplecza_data = Zaplecze.objects.filter(ssl_active=True).annotate(wp_api_key_length=Length('wp_api_key')).filter(wp_api_key_length__gt=20)

        context = {
                    "umowa": umowa, 
                    "zaplecza": zaplecza_data, 
                    "zaplecza_unique": category_data,
                    'papaj_spi': papaj_spi
                   }
        
        return render(request, 'links.html', context)
    
@method_decorator(log_user(), name='dispatch')
class LinksPanel(View):
    def get(self, request):
        try:
            user = request.user.email.split("@")[0]
            with urllib.request.urlopen(f"https://panel.verseo.pl/get_client_eichner.php?token=45h5j56k6788i4y3h57k567i54t3w6ki5y6u4u6h&pozycjoner={user}&aktywne=1") as url:
                umowy = json.load(url)
        except Exception:
            umowy = {"data": {"key":""}}


        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        context = {"umowy": umowy['data'].values(), 'papaj_spi': papaj_spi}

        return render(request, 'links_panel.html', context)
    

@method_decorator(log_user(), name='dispatch')
class UpdateProfile(APIView):
    def get(self, request):
        #get all table rows that belongs to current user
        try:
            queryset = Link.objects.filter(user=request.user.email)
        except AttributeError:
            print("Anonymus user got into user page!")
            queryset = []
        context = {
            "data": queryset[::-1]
        }
        return render(request, 'user.html', context)
    
    def post(self, request):
        user_id = request.user.id # Assuming you send user_id in the post request
        openai_api_key = request.data.get('openai_api_key')
        try:
            semstorm_api_key = request.data.get('semstorm_api_key')
        except:
            semstorm_api_key = "semstorm_key"

        try:
            account = get_object_or_404(Account, user_id=user_id)
            account.openai_api_key = openai_api_key
            account.semstorm_api_key = semstorm_api_key
        except Exception as e:
            account = Account.objects.create(user_id=user_id, openai_api_key=openai_api_key, semstorm_api_key=semstorm_api_key)
        account.save()

        return render(request, 'user.html')




class Notifications(APIView):
    def get(self, request):
        queryset = list(Banner.objects.values())
        return render(request, "partials/banners.html", {"banners": queryset})