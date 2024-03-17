from backend.models import Zaplecze, ZapleczeCategory
from django.core.exceptions import NON_FIELD_ERRORS
from django import forms
from backend.src.CreateWPblog.openai_api import OpenAI_API


class RegisterZapleczeForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=ZapleczeCategory.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = Zaplecze
        fields = ["domain", "lang", 
                  "wp_user", "wp_password", "wp_api_key", 
                  "category"]
        o = OpenAI_API(api_key="")
        widgets = {
            'lang': forms.Select(choices=[(x,x) for x in o.get_langs()],attrs={'class': 'form-control'}),
        }
        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": "%(model_name)s's %(field_labels)s are not unique.",
            }
        }


class AddZapleczeCategory(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=ZapleczeCategory.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = Zaplecze
        fields = ["category", "topic"]