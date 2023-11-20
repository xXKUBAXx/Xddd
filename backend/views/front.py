from django.shortcuts import render, get_object_or_404
from ..models import Zaplecze, Account, Link
from ..serializers import ZapleczeSerializer, AccountSerializer
from rest_framework.views import APIView
from django.views.generic import View
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from ..src.CreateWPblog.openai_api import OpenAI_API

import json

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
    

class ZapleczeUnit(View):
    def get(self, request, zaplecze_id):
        serializer = ZapleczeSerializer(Zaplecze.objects.get(id=zaplecze_id))
        
        context = {'data': serializer.data}

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        context = {
            'data': serializer.data,
            'papaj_spi': papaj_spi
        }

        return render(request, 'zaplecze.html', context)
    

class WriteLink(View):
    def detect_change(self, val1, val2):
        if val1 > val2:
            return 1
        elif val1 == val2:
            return 0
        else:
            return -1
        
    def get(self, request, umowa_id):
        umowy = json.load(open("../frazy.json"))
        for u in umowy["data"]:
            if u["id"] == umowa_id:
                umowa = u
                break

        zaplecza = [l.split("\t") for l in open("../zaplecza.tsv", encoding="utf-8").read().split("\n") if len(l.split("\t")[-1])>20]

        zaplecza_unique = list(set([z[0] for z in zaplecza]))

        visibility = [v.split("\t") for v in open("../visibility_data.tsv", encoding="utf-8").read().split("\n")]

        zaplecza_data = {}
        for z in zaplecza:
            zaplecza_data[z[1]] = {
                "domain": z[1].lower(),
                "topic": z[0], 
                "login": z[2],
                "wp_password": z[3],
                "wp_api_key": z[4],
                "date": ""
            }
        
        for v in visibility:
            dom = v[0].lower()
            try:
                if zaplecza_data[dom]["date"] == "":
                    zaplecza_data[dom].update({
                        "date": v[1],
                        "top3": v[2],
                        "top3_growth": 0,
                        "top10": v[3],
                        "top10_growth": 0,
                        "top50": v[4],
                        "top50_growth": 0
                    })
                elif zaplecza_data[dom]["date"] > v[1]:
                    top3_growth = self.detect_change(zaplecza_data[dom]["top3"], v[2])
                    top10_growth = self.detect_change(zaplecza_data[dom]["top10"], v[3])
                    top50_growth = self.detect_change(zaplecza_data[dom]["top50"], v[4])
                    zaplecza_data[dom].update({
                        "date": v[1],
                        "top3_growth": top3_growth,
                        "top10_growth": top10_growth,
                        "top50_growth": top50_growth
                    })
                else:
                    top3_growth = self.detect_change(v[2], zaplecza_data[dom]["top3"])
                    top10_growth = self.detect_change(v[3], zaplecza_data[dom]["top10"])
                    top50_growth = self.detect_change(v[4], zaplecza_data[dom]["top50"])
                    zaplecza_data[dom].update({
                        "date": v[1],
                        "top3": v[2],
                        "top3_growth": top3_growth,
                        "top10": v[3],
                        "top10_growth": top10_growth,
                        "top50": v[4],
                        "top50_growth": top50_growth
                    })
            except:
                pass

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        context = {
                    "umowa": umowa, 
                    "zaplecza": zaplecza_data, 
                    "zaplecza_unique": sorted(zaplecza_unique),
                    'papaj_spi': papaj_spi
                   }
        
        return render(request, 'links.html', context)
    

class LinksPanel(View):
    def get(self, request):
        umowy = json.load(open("../umowy.json"))

        try:
            papaj_spi = User.objects.get(username='papaj_spi')
        except User.DoesNotExist:
            papaj_spi = None

        context = {"umowy": umowy['data'].values(), 'papaj_spi': papaj_spi}

        return render(request, 'links_panel.html', context)
    

class UpdateProfile(APIView):
    def get(self, request):
        #get all table rows that belongs to current user
        queryset = Link.objects.filter(user=request.user.email)
        context = {
            "data": queryset
        }
        return render(request, 'user.html', context)
    
    def post(self, request):
        user_id = request.user.id # Assuming you send user_id in the post request
        openai_api_key = request.data.get('openai_api_key')
        semstorm_api_key = request.data.get('semstorm_api_key')

        account = get_object_or_404(Account, user_id=user_id)
        account.openai_api_key = openai_api_key
        account.semstorm_api_key = semstorm_api_key
        account.save()

        return render(request, 'user.html')
