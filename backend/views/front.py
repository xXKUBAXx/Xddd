from django.shortcuts import render
from ..models import Zaplecze, Account
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
        context = {'queryset': queryset[::-1], 'social_data': data}
        return render(request, 'index.html', context)
    

class CreateZaplecze(View):
    def get(self, request):
        try:
            data = SocialAccount.objects.get(user=request.user).extra_data
        except:
            data = {}
        langs = OpenAI_API("").get_langs()
        context = {'social_data': data, 'langs': langs}
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
        context = {'social_data': data, 'data': serializer.data}
        return render(request, 'update.html', context)
    

class ZapleczeUnit(View):
    def get(self, request, zaplecze_id):
        serializer = ZapleczeSerializer(Zaplecze.objects.get(id=zaplecze_id))
        
        context = {'data': serializer.data}

        return render(request, 'zaplecze.html', context)
    

class WriteLink(View):
    def get(self, request, umowa_id):
        umowy = json.load(open("../frazy.json"))
        for u in umowy["data"]:
            if u["id"] == umowa_id:
                umowa = u
                break
        context = {'umowa': umowa}
        
        return render(request, 'links.html', context)
    

class LinksPanel(View):
    def get(self, request):
        umowy = json.load(open("../umowy.json"))
        context = {"umowy": umowy['data'].values()}

        return render(request, 'links_panel.html', context)
    

class UpdateProfile(APIView):
    def get(self, request):
        return render(request, 'user.html')
    
    def post(self, request):
        user = Account.objects.get(id=request.user.id)
        print(user.openai_api_key)
        user.openai_api_key = request.data.get("openai_api_key")
        user.save()
        serializer = AccountSerializer(user)
        data = serializer.data
        data['openai_api_key'] = request.data.get("openai_api_key")
        serializer = AccountSerializer(instance=user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

        return render(request, 'user.html')
