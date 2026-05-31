from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('agendar/<int:consulta_id>/', views.agendar_consulta, name='agendar_consulta'),
    path('chat/<int:consulta_id>/', views.chat_consulta, name='chat_consulta'),
    path('solicitar/', views.solicitar_consulta, name='solicitar_consulta'),
]
