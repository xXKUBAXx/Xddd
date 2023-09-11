from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from django.views.generic import View
from allauth.socialaccount.models import SocialAccount


class Front(View):
    def get(self, request):
        queryset = Zaplecze.objects.values()
        try:
            data = SocialAccount.objects.get(user=request.user).extra_data
        except:
            data = {}
        context = {'queryset': queryset, 'social_data': data}
        return render(request, 'index.html', context)
    

class CreateZaplecze(View):
    def get(self, request):
        try:
            data = SocialAccount.objects.get(user=request.user).extra_data
        except:
            data = {}
        context = {'social_data': data}
        return render(request, 'create.html', context)
    

class ZapleczeUnit(View):
    def get(self, request, zaplecze_id):
        serializer = ZapleczeSerializer(Zaplecze.objects.get(id=zaplecze_id))
        
        context = {'data': serializer.data}

        return render(request, 'zaplecze.html', context)