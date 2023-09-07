from django.urls import path
from . import views


urlpatterns = [
    path('api/all/', views.ZapleczeAPIView.as_view()),
    path('api/<int:zaplecze_id>/', views.ZapleczeAPIDetail.as_view()),
    path('api/create/<int:zaplecze_id>/domain/', views.ZapleczeCreateDomain.as_view()),
    path('api/create/<int:zaplecze_id>/db/', views.ZapleczeCreateDB.as_view()),
    path('api/create/<int:zaplecze_id>/ftp/', views.ZapleczeCreateFTP.as_view()),
    path('api/create/<int:zaplecze_id>/setup/', views.ZapleczeCreateSetupWP.as_view()),
    path('api/create/<int:zaplecze_id>/tweak/', views.ZapleczeCreateTweakWP.as_view()),
    path('api/create/<int:zaplecze_id>/wp_api/', views.ZapleczeCreateWPapi.as_view()),
    path('api/structure/<int:zaplecze_id>/', views.ZapleczeAPIStructure.as_view()),
    path('', views.Front.as_view()),
    path('<int:zaplecze_id>/', views.ZapleczeUnit.as_view()),
    path('create/', views.CreateZaplecze.as_view())
]