from django.urls import path
from . import views


urlpatterns = [
    path('api/all/', views.ZapleczeAPIView.as_view()),
    path('api/<int:zaplecze_id>/', views.ZapleczeAPIDetail.as_view()),
    path('api/create/', views.ZapleczeCreateAll.as_view()),
    path('api/create/<int:zaplecze_id>/domain/', views.ZapleczeCreateDomain.as_view()),
    path('api/create/<int:zaplecze_id>/db/', views.ZapleczeCreateDB.as_view()),
    path('api/create/<int:zaplecze_id>/ftp/', views.ZapleczeCreateFTP.as_view()),
    path('api/create/<int:zaplecze_id>/setup/', views.ZapleczeCreateSetupWP.as_view()),
    path('api/create/<int:zaplecze_id>/tweak/', views.ZapleczeCreateTweakWP.as_view()),
    path('api/create/<int:zaplecze_id>/wp_api/', views.ZapleczeCreateWPapi.as_view()),
    path('api/create/<int:zaplecze_id>/zaplecze_classic/', views.ZapleczeClassic.as_view()),
    path('api/create/<int:zaplecze_id>/zaplecze_comp/', views.ZapleczeComp.as_view()),
    path('api/structure/<int:zaplecze_id>/', views.ZapleczeAPIStructure.as_view()),
    path('api/structure/', views.AnyZapleczeAPIStructure.as_view()),
    path('api/write/<int:zaplecze_id>/', views.ZapleczeWrite.as_view()),
    path('api/write/', views.AnyZapleczeWrite.as_view()),
    path('api/links/', views.ManyZapleczesWrite.as_view()),
    path('', views.Front.as_view()),
    path('logout', views.logout_view),
    path('user/', views.UpdateProfile.as_view()),
    path('create/', views.CreateZaplecze.as_view()),
    path('links_panel/', views.LinksPanel.as_view()),
    path('links/<int:umowa_id>/', views.WriteLink.as_view()),
    path('<int:zaplecze_id>/', views.ZapleczeUnit.as_view()),
    path('<int:zaplecze_id>/update/', views.UpdateZaplecze.as_view())
]