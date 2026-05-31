from django.contrib import admin
from .models import (
    Usuario, Instituicao, Terapeuta, Matricula, 
    AutorizacaoConsulta, Agendamentos, Consultas, 
    Formularios, Chats, Mensagem, FeedbackAvaliacao, Relatorios
)

admin.site.register(Usuario)
admin.site.register(Instituicao)
admin.site.register(Terapeuta)
admin.site.register(Matricula)
admin.site.register(AutorizacaoConsulta)
admin.site.register(Agendamentos)
admin.site.register(Consultas)
admin.site.register(Formularios)
admin.site.register(Chats)
admin.site.register(Mensagem)
admin.site.register(FeedbackAvaliacao)
admin.site.register(Relatorios)