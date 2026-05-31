from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import IntegrityError 
from .models import Usuario, Consulta, Mensagem
from .forms import RegistroForm, SolicitarConsultaForm, AgendarConsultaForm, MensagemForm 

def index(request):
    """ View de Login """
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
    """ View de Registro usando o RegistroForm do Django """
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
                    
                user.save()
                
                messages.success(request, "Conta criada com sucesso! Por favor, faça o login.")
                return redirect("index")
                
            except IntegrityError:
                messages.error(request, "Ocorreu um erro ao criar a conta. Tente novamente.")
                

        messages.error(request, "Houve um erro na validação dos dados.")
        
    
    form = RegistroForm()
    
    return render(request, "register.html", {"form": form})

def logout_view(request):
    """ View de Logout """
    logout(request)
    messages.info(request, "Você foi desconectado(a).")
    return redirect("index")



@login_required
def home(request):
    """ View Home que direciona o conteúdo baseado no tipo de usuário. """
    
    if request.user.is_psicologo:
        consultas_pendentes = Consulta.objects.filter(
            psicologo=request.user, 
            status="pendente"
        ).order_by('criado_em')
        
        consultas_agendadas = Consulta.objects.filter(
            psicologo=request.user
        ).exclude(status="pendente").order_by('data_hora')
        
        context = {
            "consultas_pendentes": consultas_pendentes,
            "consultas_agendadas": consultas_agendadas,
        }
        
    else:
        # Paciente: Apenas suas consultas
        consultas = Consulta.objects.filter(
            paciente=request.user
        ).order_by('-criado_em')
        
        context = {
            "consultas": consultas,
        }
    

    return render(request, "home.html", context) 



@login_required
def solicitar_consulta(request):
    """ View para o Paciente solicitar uma nova consulta """
    
    if request.user.is_psicologo:
        messages.error(request, "Psicólogos não podem solicitar consultas. Apenas pacientes.")
        return redirect("home")
        
    if request.method == "POST":
        form = SolicitarConsultaForm(request.POST) 
        
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.paciente = request.user 
            consulta.status = "pendente"
            # data_hora é deixado NULO
            
            consulta.save()
            messages.success(request, "Solicitação enviada! O psicólogo irá agendar a consulta.")
            return redirect("home")
    
    else:
        form = SolicitarConsultaForm()
        
    return render(request, "solicitar_consulta.html", {"form": form})


@login_required
def agendar_consulta(request, consulta_id):
    """ View para o Psicólogo agendar uma consulta pendente. """
    
    consulta = get_object_or_404(
        Consulta, 
        id=consulta_id, 
        status='pendente',
        psicologo=request.user
    )


    if not request.user.is_psicologo:
        messages.error(request, "Você não tem permissão para agendar consultas.")
        return redirect("home")

    if request.method == "POST":
        form = AgendarConsultaForm(request.POST, instance=consulta)
        
        if form.is_valid():
            form.save() 
            messages.success(request, f"Consulta agendada para {consulta.data_hora.strftime('%d/%m/%Y às %H:%M')}!")
            return redirect("home")
    
    else:
        form = AgendarConsultaForm(instance=consulta)
        
    return render(request, "agendar_consulta.html", {"consulta": consulta, "form": form})


@login_required
def chat_consulta(request, consulta_id):
    """ View para o Chat (mensagens) """
    
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    if request.user not in [consulta.paciente, consulta.psicologo]:
        messages.error(request, "Você não tem acesso a este chat.")
        return redirect("home")
        
    mensagens = consulta.mensagens.all().order_by("criado_em")
    
    if request.method == "POST":
        form = MensagemForm(request.POST)
        if form.is_valid():
            mensagem = form.save(commit=False)
            mensagem.consulta = consulta
            mensagem.remetente = request.user
            mensagem.save()
            
            return redirect("chat_consulta", consulta_id=consulta.id) 
            
    else:
        form = MensagemForm()
        
    return render(request, "chat_consulta.html", {
        "consulta": consulta, 
        "mensagens": mensagens, 
        "form": form
    })