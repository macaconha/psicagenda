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
                user = Usuario.objects.create_user(
                    username=data['username'],
                    email=data.get('email', ''), 
                    password=data['password']
                )
                
                if data['tipo_usuario'] == "psicologo":
                    user.is_psicologo = True
                    user.save() # Salva o usuário primeiro para gerar o ID
                    
                    # 🟢 ADICIONE ESTA LINHA AQUI:
                    # Cria automaticamente o perfil vinculado na tabela Terapeuta
                    Terapeuta.objects.create(usuario=user)
                else:
                    user.save()

                messages.success(request, "Conta criada com sucesso! Por favor, faça o login.")
                return redirect("index")
            except Exception as e:
                print(f"Erro no registro: {e}") # Ajuda a debugar no terminal se falhar
                messages.error(request, "Ocorreu um erro ao criar a conta. Tente novamente.")
    else:
        form = RegistroForm()
    return render(request, "register.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "Você foi desconectado(a).")
    return redirect("index")

# Para isto (Bem mais seguro e correto):
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

# views.py

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
            # 🔴 ADICIONE ESSA LINHA AQUI ABAIXO:
            print("ERROS DO FORMULÁRIO:", form.errors)
            
    else:
        form = SolicitarConsultaForm()
    return render(request, "solicitar_consulta.html", {"form": form})

@login_required
def agendar_consulta(request, consulta_id):
    # Procura o agendamento pendente para transformá-lo em uma sessão oficial
    agendamento = get_object_or_404(Agendamentos, id=consulta_id, status='pendente')
    if request.method == "POST":
        form = AgendarConsultaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.agendamento = agendamento
            consulta.save()
            
            agendamento.status = "confirmado"
            agendamento.save()
            messages.success(request, "Consulta agendada com sucesso!")
            return redirect("home")
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