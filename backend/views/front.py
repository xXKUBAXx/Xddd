from django.shortcuts import render
from ..models import Zaplecze
from ..serializers import ZapleczeSerializer
from django.views.generic import View



class Front(View):
    def get(self, request):
        queryset = Zaplecze.objects.values()
        context = {'queryset': queryset}
        return render(request, 'index.html', context)
    

class CreateZaplecze(View):
    def get(self, request):
        return render(request, 'create.html')
    

class ZapleczeUnit(View):
    def get(self, request, zaplecze_id):
        serializer = ZapleczeSerializer(Zaplecze.objects.get(id=zaplecze_id))
        
        context = {'data': serializer.data}

        return render(request, 'zaplecze.html', context)