from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate  
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

# Importe os seus modelos e formulários necessários
from .models import Usuario, Terapeuta, Matricula, Agendamentos, Mensagem, Chats, Consultas, FeedbackAvaliacao
from .forms import RegistroForm, SolicitarConsultaForm, AgendarConsultaForm

# ==============================================================================
# PÁGINA INICIAL / DIRECIONAMENTO
# ==============================================================================
def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('register')


# ==============================================================================
# SISTEMA DE LOGIN 
# ==============================================================================
def login_view(request):
    """
    Gerencia o acesso de usuários já cadastrados.
    """
    if request.user.is_authenticated:
        return redirect('home')

    erro = None
    if request.method == 'POST':
        usuario_input = request.POST.get('username')
        senha_input = request.POST.get('password')
        
        user = authenticate(request, username=usuario_input, password=senha_input)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            erro = "Usuário ou senha inválidos."

    return render(request, 'index.html', {'erro': erro})


# ==============================================================================
# SISTEMA DE LOGOUT 
# ==============================================================================
def logout_view(request):
    logout(request)
    return redirect('register')


# ==============================================================================
# DASHBOARD PRINCIPAL / HOME
# ==============================================================================
@login_required
def home(request):
    contexto = {}
    
    if request.user.is_psicologo:
        terapeuta = get_object_or_404(Terapeuta, usuario=request.user)
        
        contexto['consultas_pendentes'] = Agendamentos.objects.filter(
            terapeuta=terapeuta, 
            status='pendente'
        ).order_by('-criado_em')
        
        contexto['consultas_agendadas'] = Agendamentos.objects.filter(
            terapeuta=terapeuta, 
            status='agendada'
        ).order_by('data_hora_sugerida')
        
    else:
        contexto['consultas'] = Agendamentos.objects.filter(
            paciente=request.user
        ).order_by('-criado_em')
        
        try:
            contexto['matricula'] = request.user.matricula
        except ObjectDoesNotExist:
            contexto['matricula'] = None

    return render(request, 'home.html', contexto)


# ==============================================================================
# EFETUAR O AGENDAMENTO DA CONSULTA
# ==============================================================================
@login_required
def agendar_consulta(request, consulta_id):
    if not request.user.is_psicologo:
        return redirect('home')
        
    # Busca o agendamento pendente que o aluno fez
    agendamento = get_object_or_404(Agendamentos, id=consulta_id)

    if request.method == 'POST':
        form = AgendarConsultaForm(request.POST)
        if form.is_valid():
            consulta_final = form.save(commit=False)
            
            # Vincula o agendamento à consulta
            consulta_final.agendamento = agendamento
            consulta_final.save()
            
            # Atualiza o status do agendamento original para 'agendada'
            agendamento.status = 'agendada'
            agendamento.save()
            
            return redirect('home')
    else:
        form = AgendarConsultaForm()

    return render(request, 'agendar_consulta.html', {
        'form': form,
        'agendamento': agendamento
    })


# ==============================================================================
# SALA DE CHAT DA CONSULTA + FEEDBACK & RELATÓRIO PÓS-SESSÃO
# ==============================================================================
@login_required
def chat_consulta(request, consulta_id):
    # 1. Busca o agendamento atual para saber quem é o paciente e o terapeuta
    agendamento = get_object_or_404(Agendamentos, id=consulta_id)
    
    # Bloqueia o acesso se o usuário logado não fizer parte dessa consulta
    if request.user != agendamento.paciente and request.user != agendamento.terapeuta.usuario:
        return redirect('home')
        
    # 2. Busca ou Cria a sala de chat baseando-se no par Paciente + Terapeuta
    chat_objeto, criado = Chats.objects.get_or_create(
        paciente=agendamento.paciente,
        terapeuta=agendamento.terapeuta
    )

    # 3. Localiza a instância de Consulta real associada
    consulta_real = getattr(agendamento, 'consulta_vinculada', None)

    # 4. Verifica se o horário agendado da consulta já ficou no passado
    consulta_encerrada = agendamento.data_hora_sugerida < timezone.now()
        
    if request.method == 'POST':
        # Caso A: Envio normal de nova mensagem no Chat
        if 'mensagem_texto' in request.POST:
            texto = request.POST.get('mensagem_texto')
            if texto:
                Mensagem.objects.create(
                    chat=chat_objeto,
                    remetente=request.user,
                    conteudo=texto
                )
            return redirect('chat_consulta', consulta_id=agendamento.id)

        # Caso B: Paciente enviando o Feedback (Apenas após o horário final)
        elif 'feedback_texto' in request.POST and consulta_encerrada and request.user == agendamento.paciente:
            if consulta_real:
                FeedbackAvaliacao.objects.update_or_create(
                    consulta=consulta_real,
                    defaults={
                        'nota_atendimento': request.POST.get('feedback_nota', 5),
                        'comentario_paciente': request.POST.get('feedback_texto')
                    }
                )
            return redirect('chat_consulta', consulta_id=agendamento.id)

        # Caso C: Psicólogo registrando Relatório Clínico Privado
        elif 'relatorio_texto' in request.POST and consulta_encerrada and request.user.is_psicologo:
            if consulta_real:
                consulta_real.relatorio_clinico = request.POST.get('relatorio_texto')
                consulta_real.status = "realizada"
                consulta_real.save()
            return redirect('chat_consulta', consulta_id=agendamento.id)

    # Busca o histórico de mensagens desse chat específico
    mensagens_historico = Mensagem.objects.filter(chat=chat_objeto).order_by('criado_em')
        
    contexto = {
        'consulta': agendamento,
        'consulta_real': consulta_real,
        'mensagens': mensagens_historico,
        'consulta_encerrada': consulta_encerrada,
    }
    
    return render(request, 'chat_consulta.html', contexto)


# ==============================================================================
# VIEW DE REGISTRO (VINCULADA AO SEU REGISTROFORM)
# ==============================================================================
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            tipo_usuario = form.cleaned_data['tipo_usuario']
            instituicao = form.cleaned_data['instituicao']
            
            user = Usuario.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            
            if tipo_usuario == 'psicologo':
                user.is_psicologo = True
                user.save()
                
                Terapeuta.objects.create(
                    usuario=user,
                    instituicao=instituicao,
                    crp="Pendente"
                )
            else:  # Caso seja 'paciente' (Aluno)
                user.is_psicologo = False
                user.save()
                
                codigo_mat = form.cleaned_data['codigo_matricula']
                Matricula.objects.create(
                    aluno=user,
                    instituicao=instituicao,
                    codigo_matricula=codigo_mat,
                    ativo=True
                )
            
            login(request, user)
            return redirect('home')
    else:
        form = RegistroForm()
        
    return render(request, 'register.html', {'form': form})


# ==============================================================================
# VIEW DE SOLICITAR CONSULTA 
# ==============================================================================
@login_required
def solicitar_consulta_view(request):
    if request.user.is_psicologo:
        return redirect('home')

    # Busca a matrícula do aluno para descobrir a instituição dele
    try:
        matricula_aluno = request.user.matricula
        if not matricula_aluno.ativo:
            return render(request, 'erro_matricula.html', {
                'mensagem': "Sua matrícula escolar está inativa. Procure a secretaria da escola."
            })
        instituicao_aluno = matricula_aluno.instituicao
    except ObjectDoesNotExist:
        return render(request, 'erro_matricula.html', {
            'mensagem': "Sua matrícula escolar não foi localizada. Procure a secretaria da escola."
        })

    if request.method == 'POST':
       if request.method == 'POST':
        # 🟢 REMOVIDO O 'Sample=None' DAQUI:
        form = SolicitarConsultaForm(request.POST, instituicao_aluno=instituicao_aluno)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.paciente = request.user
            agendamento.status = 'pendente'
            agendamento.save()
            return redirect('home')
    else:
        form = SolicitarConsultaForm(instituicao_aluno=instituicao_aluno)

    return render(request, 'solicitar_consulta.html', {'form': form})

solicitar_consulta = solicitar_consulta_view


# ==============================================================================
# LISTA DE MATRÍCULAS 
# ==============================================================================
@login_required
def lista_matriculas(request):
    if not request.user.is_psicologo:
        return redirect('home')

    matriculas = Matricula.objects.all().order_by('aluno__username')
    return render(request, 'lista_matriculas.html', {'matriculas': matriculas})


# ==============================================================================
# ALTERNAR STATUS DA MATRÍCULA
# ==============================================================================
@login_required
def alternar_status_matricula(request, matricula_id):
    if not request.user.is_psicologo:
        return redirect('home')
        
    matricula = get_object_or_404(Matricula, id=matricula_id)
    matricula.ativo = not matricula.ativo
    matricula.save()
    
    return redirect('lista_matriculas')