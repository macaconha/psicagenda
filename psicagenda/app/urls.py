from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),  # 🟢 ADICIONE ESTA LINHA
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('agendar/<int:consulta_id>/', views.agendar_consulta, name='agendar_consulta'),
    path('chat/<int:consulta_id>/', views.chat_consulta, name='chat_consulta'),
    path('solicitar/', views.solicitar_consulta, name='solicitar_consulta'),
    path('matriculas/', views.lista_matriculas, name='lista_matriculas'),
    path('matriculas/status/<int:matricula_id>/', views.alternar_status_matricula, name='alternar_status_matricula'),
]
