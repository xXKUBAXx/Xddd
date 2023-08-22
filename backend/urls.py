from django.urls import path
from . import views


urlpatterns = [
    path('api/all/', views.ZapleczeAPIView.as_view()),
    path('api/<int:zaplecze_id>/', views.ZapleczeAPIDetail.as_view()),
    path('api/create/<int:zaplecze_id>/', views.ZapleczeAPICreate.as_view()),
    path('api/structure/<int:zaplecze_id>/', views.ZapleczeAPIStructure.as_view()),
    path('', views.Front.as_view()),
    path('<int:zaplecze_id>/', views.ZapleczeUnit.as_view()),
    path('create/', views.CreateZaplecze.as_view())
]