from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Usuario(AbstractUser):
    # Campo para diferenciar Pacientes (False) de Psicólogos (True)
    is_psicologo = models.BooleanField(default=False)
    telefone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    foto_perfil = models.ImageField(upload_to="usuarios/", blank=True, null=True)

    def __str__(self):
        return self.username

class Consulta(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("agendada", "Agendada"),  
        ("cancelada", "Cancelada"),
        ("realizada", "Realizada"),
    ]
    
    paciente = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name="consultas_paciente",
        limit_choices_to={'is_psicologo': False} 
    )
    
    psicologo = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name="consultas_psicologo",
        limit_choices_to={'is_psicologo': True} 
    )
    
    data_hora = models.DateTimeField(null=True, blank=True) 
    criado_em = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    descricao = models.TextField(blank=True) # Descrição/Motivo da solicitação

    def __str__(self):
        return f"Consulta {self.id} - {self.paciente.username} com {self.psicologo.username} ({self.status})"

class Mensagem(models.Model):
    consulta = models.ForeignKey(
        Consulta, 
        on_delete=models.CASCADE, 
        related_name="mensagens"
    )
    remetente = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE
    ) 
    conteudo = models.TextField()
    criado_em = models.DateTimeField(default=timezone.now) 

    def __str__(self):
        return f"Mensagem de {self.remetente.username} em {self.criado_em.strftime('%d/%m %H:%M')}"