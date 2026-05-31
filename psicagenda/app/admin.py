from django.contrib import admin
from .models import Usuario, Consulta, Mensagem

admin.site.register(Usuario)
admin.site.register(Consulta)
admin.site.register(Mensagem)