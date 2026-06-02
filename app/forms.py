from django import forms
from django.contrib.auth import get_user_model
from django.forms.widgets import DateTimeInput, PasswordInput
from django.core.exceptions import ValidationError
# IMPORTANTE: Garanta que 'Instituicao' esteja listada aqui nos imports dos seus modelos
from .models import Usuario, Agendamentos, Consultas, Mensagem, FeedbackAvaliacao, Instituicao

User = get_user_model()

class RegistroForm(forms.Form):
    TIPO_USUARIO_CHOICES = (
        ('paciente', 'Paciente'),
        ('psicologo', 'Psicólogo'),
    )
    username = forms.CharField(max_length=150, label='Nome de Usuário')
    email = forms.EmailField(required=True, label='Email')
    password = forms.CharField(widget=PasswordInput, label='Senha')
    confirm_password = forms.CharField(widget=PasswordInput, label='Confirmar Senha')
    
    tipo_usuario = forms.ChoiceField(
        choices=TIPO_USUARIO_CHOICES, 
        label='Você é um(a)...',
        required=True
    )
    
    # 🟢 NOVO CAMPO ADICIONADO:
    # Busca todas as instituições para listar no select do formulário.
    instituicao = forms.ModelChoiceField(
        queryset=Instituicao.objects.all(),
        required=False,
        label='Instituição (Apenas se você for Psicólogo)',
        empty_label='Selecione uma instituição'
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username__iexact=username).exists(): 
            raise ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este email já está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError("As senhas não coincidem.")
        return cleaned_data


class SolicitarConsultaForm(forms.ModelForm):
    class Meta:
        model = Agendamentos
        # Agora o Django vai reconhecer a 'descricao' com sucesso!
        fields = ['terapeuta', 'data_hora_sugerida', 'descricao']
        widgets = {
            'data_hora_sugerida': DateTimeInput(attrs={'type': 'datetime-local'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Conte um pouco sobre o motivo da consulta...'}),
        }


class AgendarConsultaForm(forms.ModelForm):
    """
    Atualizado: Transforma um Agendamento em uma Consulta ativa.
    """
    class Meta:
        model = Consultas
        fields = ['status', 'data_hora_realizacao', 'observacoes_internas'] 
        widgets = {
            'data_hora_realizacao': DateTimeInput(attrs={'type': 'datetime-local'}),
            'observacoes_internas': forms.Textarea(attrs={'rows': 3}),
        }


class MensagemForm(forms.ModelForm):
    class Meta:
        model = Mensagem
        fields = ['conteudo']
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Digite sua mensagem...'}),
        }