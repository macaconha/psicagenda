from django import forms
from django.contrib.auth import get_user_model
from django.forms.widgets import DateTimeInput, PasswordInput
from django.core.exceptions import ValidationError
from .models import Usuario, Agendamentos, Consultas, Mensagem, FeedbackAvaliacao, Instituicao, Matricula, Terapeuta

User = get_user_model()

class RegistroForm(forms.Form):
    TIPO_USUARIO_CHOICES = (
        ('paciente', 'Aluno (Paciente)'),
        ('psicologo', 'Psicólogo / Profissional'),
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
    
    # 🟢 Agora é obrigatório para ambos (Aluno ou Psicólogo)
    instituicao = forms.ModelChoiceField(
        queryset=Instituicao.objects.all(),
        required=True,
        label='Sua Escola / Instituição',
        empty_label='Selecione a sua instituição'
    )

    # 🟢 Novo campo adicionado para coletar a matrícula do aluno no momento do cadastro
    codigo_matricula = forms.CharField(
        max_length=50,
        required=False,
        label='Código de Matrícula Escolar',
        widget=forms.TextInput(attrs={'placeholder': 'Ex: MAT-2026-0042', 'class': 'form-control'})
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
        tipo_usuario = cleaned_data.get('tipo_usuario')
        codigo_matricula = cleaned_data.get('codigo_matricula')

        # Validação de igualdade das senhas
        if password and confirm_password and password != confirm_password:
            raise ValidationError("As senhas não coincidem.")
        
        # 🟢 Validação customizada para a Opção B:
        # Se escolheu 'Aluno (Paciente)', o preenchimento da matrícula passa a ser obrigatório
        if tipo_usuario == 'paciente' and not codigo_matricula:
            self.add_error('codigo_matricula', "Alunos precisam informar o código de matrícula escolar.")

        # Evita duplicidade de código de matrícula no banco de dados
        if codigo_matricula and Matricula.objects.filter(codigo_matricula=codigo_matricula).exists():
            self.add_error('codigo_matricula', "Este código de matrícula já está cadastrado no sistema.")

        return cleaned_data


class SolicitarConsultaForm(forms.ModelForm):
    class Meta:
        model = Agendamentos
        fields = ['terapeuta', 'data_hora_sugerida', 'descricao']
        widgets = {
            'data_hora_sugerida': DateTimeInput(attrs={'type': 'datetime-local'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Conte um pouco sobre o motivo da consulta...'}),
        }

    # Construtor para restringir os psicólogos à mesma instituição do aluno
    def __init__(self, *args, **kwargs):
        instituicao_aluno = kwargs.pop('instituicao_aluno', None)
        super().__init__(*args, **kwargs)
        
        if substituicao_aluno := instituicao_aluno:
            self.fields['terapeuta'].queryset = Terapeuta.objects.filter(
                instituicao=substituicao_aluno
            ).select_related('usuario')
            self.fields['terapeuta'].empty_label = "Selecione um psicólogo da sua escola"


class AgendarConsultaForm(forms.ModelForm):
    """
    Transforma um Agendamento em uma Consulta ativa.
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


# ==============================================================================
# REF02: GERENCIAR MATRÍCULA (SECRETARIA / ADMIN)
# ==============================================================================
class MatriculaForm(forms.ModelForm):
    class Meta:
        model = Matricula
        # 🟢 Retornado para a lista explícita com segurança após rodar as migrações
        fields = ['aluno', 'instituicao', 'codigo_matricula', 'ativo']
        labels = {
            'aluno': 'Aluno (Paciente)',
            'instituicao': 'Escola / Instituição',
            'codigo_matricula': 'Código de Matrícula Escolar',
            'ativo': 'Matrícula Ativa (Permite solicitar atendimentos)'
        }
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'instituicao': forms.Select(attrs={'class': 'form-control'}),
            'codigo_matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: MAT-2026-0042'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }