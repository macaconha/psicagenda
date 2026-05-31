from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Usuario, Agendamentos, Consultas, Chats, Mensagem, Terapeuta
from .forms import RegistroForm, SolicitarConsultaForm, AgendarConsultaForm, MensagemForm 

def index(request):
    if request.user.is_authenticated:
        return redirect("home")
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password) 
        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Usuário ou senha inválidos.")
            
    return render(request, "index.html")

def register(request):
    if request.method == "POST":
        form = RegistroForm(request.POST) 
        if form.is_valid():
            data = form.cleaned_data
            try:
                # 1. Cria o usuário base na tabela Usuario
                user = Usuario.objects.create_user(
                    username=data['username'],
                    email=data.get('email', ''), 
                    password=data['password']
                )
                
                # 2. Verifica se o tipo selecionado foi psicólogo
                if data['tipo_usuario'] == "psicologo":
                    user.is_psicologo = True
                    user.save()  # Salva primeiro para gerar o ID do usuário no banco
                    
                    # Captura a instituição selecionada no formulário
                    instituicao_selecionada = data.get('instituicao')
                    
                    # Validação de segurança: Psicólogo obrigatoriamente precisa de instituição
                    if not instituicao_selecionada:
                        user.delete()  # Desfaz a criação do usuário para não deixar lixo no banco
                        messages.error(request, "Psicólogos precisam selecionar uma instituição válida.")
                        return render(request, "register.html", {"form": form})
                    
                    # 3. Cria o registro na tabela Terapeuta com a instituição vinculada
                    Terapeuta.objects.create(
                        usuario=user, 
                        instituicao=instituicao_selecionada
                    ) 
                else:
                    user.save()

                messages.success(request, "Conta criada com sucesso! Por favor, faça o login.")
                return redirect("index")
                
            except Exception as e:
                print(f"Erro ao registrar: {e}") 
                messages.error(request, "Ocorreu um erro ao criar a conta. Tente novamente.")
    else:
        form = RegistroForm()
    return render(request, "register.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "Você foi desconectado(a).")
    return redirect("index")

@login_required
def home(request):
    if request.user.is_psicologo:
        # Busca o perfil de terapeuta associado ao usuário logado
        terapeuta_perfil = getattr(request.user, 'perfil_terapeuta', None)
        
        if terapeuta_perfil:
            consultas_pendentes = Agendamentos.objects.filter(terapeuta=terapeuta_perfil, status="pendente")
            consultas_agendadas = Consultas.objects.filter(agendamento__terapeuta=terapeuta_perfil)
        else:
            consultas_pendentes = Agendamentos.objects.none()
            consultas_agendadas = Consultas.objects.none()
        
        context = {
            "consultas_pendentes": consultas_pendentes,
            "consultas_agendadas": consultas_agendadas,
        }
    else:
        consultas = Agendamentos.objects.filter(paciente=request.user).order_by('-criado_em')
        context = {
            "consultas": consultas,
        }
    return render(request, "home.html", context)

@login_required
def solicitar_consulta(request):
    if request.user.is_psicologo:
        messages.error(request, "Psicólogos não podem solicitar consultas.")
        return redirect("home")
        
    if request.method == "POST":
        form = SolicitarConsultaForm(request.POST) 
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.paciente = request.user 
            agendamento.status = "pendente"
            agendamento.save()
            messages.success(request, "Solicitação enviada com sucesso!")
            return redirect("home")
        else:
            print("ERROS DO FORMULÁRIO:", form.errors)
            
    else:
        form = SolicitarConsultaForm()
    return render(request, "solicitar_consulta.html", {"form": form})

@login_required
def agendar_consulta(request, consulta_id):
    # Procura o agendamento pendente
    agendamento = get_object_or_404(Agendamentos, id=consulta_id, status='pendente')
    
    if request.method == "POST":
        form = AgendarConsultaForm(request.POST)
        if form.is_valid():
            # 1. Salva a consulta oficial
            consulta = form.save(commit=False)
            consulta.agendamento = agendamento
            consulta.save()
            
            # 2. Atualiza o status do agendamento original para confirmado
            agendamento.status = "confirmado"
            agendamento.save()
            
            # 3. 🟢 CORREÇÃO DO ERRO DE INTEGRIDADE:
            # Passamos os dados obrigatórios usando os dados contidos no agendamento original
            Chats.objects.get_or_create(
                id=consulta.id,
                defaults={
                    'paciente': agendamento.paciente,
                    'terapeuta': agendamento.terapeuta
                }
            )

            messages.success(request, "Consulta agendada e sala de chat criada com sucesso!")
            return redirect("home")
        else:
            print("ERROS DO AGENDAMENTO:", form.errors)
    else:
        form = AgendarConsultaForm()
        
    return render(request, "agendar_consulta.html", {"form": form})

@login_required
def chat_consulta(request, consulta_id):
    chat = get_object_or_404(Chats, id=consulta_id)
    mensagens = chat.mensagens.all().order_by("criado_em")
    if request.method == "POST":
        form = MensagemForm(request.POST)
        if form.is_valid():
            mensagem = form.save(commit=False)
            mensagem.chat = chat
            mensagem.remetente = request.user
            mensagem.save()
            return redirect("chat_consulta", consulta_id=chat.id) 
    else:
        form = MensagemForm()
    return render(request, "chat_consulta.html", {"consulta": chat, "mensagens": mensagens, "form": form})