from django import forms
from .models import Consulta, Mensagem, Usuario 
from django.contrib.auth import get_user_model
from django.forms.widgets import DateTimeInput, PasswordInput
from django.core.exceptions import ValidationError


User = get_user_model()


class RegistroForm(forms.Form):
    """
    Formulário para criar um novo usuário e definir seu tipo (Paciente/Psicólogo).
    """
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

    def clean_username(self):
        """ Valida se o username já existe. """
        username = self.cleaned_data.get('username')

        if Usuario.objects.filter(username__iexact=username).exists(): 
            raise ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean_email(self):
        """ Valida se o email já existe. """
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este email já está registrado.")
        return email

    def clean(self):
        """ Validação global para verificar se as senhas coincidem. """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("As senhas não coincidem.")
        
        return cleaned_data


class SolicitarConsultaForm(forms.ModelForm):
    """
    Formulário para Pacientes solicitarem uma consulta.
    Permite selecionar apenas usuários que são psicólogos.
    """
    class Meta:
        model = Consulta
        fields = ['psicologo', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.fields['psicologo'].queryset = User.objects.filter(
            is_psicologo=True
        ).order_by('username')


class AgendarConsultaForm(forms.ModelForm):
    """
    Formulário para Psicólogos agendarem (definirem a data/hora) uma consulta solicitada.
    """
    data_hora_agendamento = forms.DateTimeField(
        label="Data e Hora do Agendamento",
        widget=DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True
    )

    class Meta:
        model = Consulta
        fields = ['status'] 
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            ('agendada', 'Agendada'), 
            ('cancelada', 'Cancelar Consulta')
        ]
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.data_hora = self.cleaned_data.get('data_hora_agendamento')
        
        if instance.data_hora and instance.status == 'pendente':
            instance.status = 'agendada' 

        if commit:
            instance.save()
        return instance


class MensagemForm(forms.ModelForm):
    """
    Formulário simples para o envio de mensagens no chat.
    """
    class Meta:
        model = Mensagem
        fields = ['conteudo']
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Digite sua mensagem...'}),
        }