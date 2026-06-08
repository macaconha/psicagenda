from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# ==============================================================================
# REF01 & REF13: GERENCIAR USUÁRIO / SISTEMA DE LOGIN
# ==============================================================================
class Usuario(AbstractUser):
    # Diferencia Alunos (Pacientes), Psicólogos/Terapeutas e Administradores da Instituição
    is_psicologo = models.BooleanField(default=False)
    is_admin_instituicao = models.BooleanField(default=False)
    telefone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    foto_perfil = models.ImageField(upload_to="usuarios/", blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({'Psicólogo' if self.is_psicologo else 'Aluno (Paciente)'})"


# ==============================================================================
# REF03: GERENCIAR INSTITUIÇÃO
# ==============================================================================
class Instituicao(models.Model):
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome


# ==============================================================================
# REF08: GERENCIAR TERAPEUTA
# ==============================================================================
class Terapeuta(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil_terapeuta")
    instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE, related_name="tererapeutas")
    crp = models.CharField(max_length=20, verbose_name="Registro CRP ou de Estudante/Estagiário")
    especialidade = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Terapeuta: {self.usuario.username} - CRP: {self.crp}"


# ==============================================================================
# REF02: GERENCIAR MATRÍCULA (VINCULADA AO ALUNO/PACIENTE DA ESCOLA)
# ==============================================================================
class Matricula(models.Model):
    # Vincula a matrícula diretamente ao Aluno (Paciente)
    aluno = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name="matricula",
        limit_choices_to={'is_psicologo': False, 'is_admin_instituicao': False}
    )
    # Vincula o Aluno à sua respectiva Escola/Instituição
    instituicao = models.ForeignKey(
        Instituicao, 
        on_delete=models.CASCADE, 
        related_name="matriculas_alunos", 
        null=True, 
        blank=True
    )
    codigo_matricula = models.CharField(max_length=50, unique=True)
    data_inicio = models.DateField(default=timezone.now)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        esc = self.instituicao.nome if self.instituicao else "Sem Escola"
        return f"Matrícula {self.codigo_matricula} - Aluno: {self.aluno.username} ({esc})"


# ==============================================================================
# REF04: GERENCIAR AUTORIZAÇÃO PARA CONSULTA
# ==============================================================================
class AutorizacaoConsulta(models.Model):
    STATUS_AUTORIZACAO = [
        ("analise", "Em Análise"),
        ("autorizado", "Autorizado"),
        ("negado", "Negado"),
    ]
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="autorizacoes", limit_choices_to={'is_psicologo': False})
    solicitado_em = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_AUTORIZACAO, default="analise")
    justificativa = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Autorização {self.id} - Paciente: {self.paciente.username} ({self.status})"


# ==============================================================================
# REF05: GERENCIAR AGENDAMENTOS
# ==============================================================================
class Agendamentos(models.Model):
    STATUS_AGENDAMENTO = [
        ("pendente", "Aguardando Confirmação"),
        ("confirmado", "Confirmado"),
        ("cancelado", "Cancelado"),
    ]
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="agendamentos_paciente", limit_choices_to={'is_psicologo': False})
    terapeuta = models.ForeignKey(Terapeuta, on_delete=models.CASCADE, related_name="agendamentos_terapeuta")
    data_hora_sugerida = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_AGENDAMENTO, default="pendente")
    criado_em = models.DateTimeField(default=timezone.now)
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição do Motivo")

    def __str__(self):
        return f"Agendamento {self.id} - {self.paciente.username} com {self.terapeuta.usuario.username}"


# ==============================================================================
# REF06: GERENCIAR CONSULTAS
# ==============================================================================
class Consultas(models.Model):
    STATUS_CONSULTA = [
        ("agendada", "Agendada"),
        ("realizada", "Realizada"),
        ("ausente", "Paciente Faltou"),
        ("cancelada", "Cancelada"),
    ]
    agendamento = models.OneToOneField(Agendamentos, on_delete=models.CASCADE, related_name="consulta_vinculada")
    data_hora_realizacao = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CONSULTA, default="agendada")
    observacoes_internas = models.TextField(blank=True, null=True) # Visível apenas para o terapeuta
    
    # Parecer clínico salvo apenas para o próprio psicólogo e a instituição
    relatorio_clinico = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Consulta {self.id} (Ref. Agendamento {self.agendamento.id}) - Status: {self.status}"


# ==============================================================================
# REF07: GERENCIAR FORMULÁRIOS
# ==============================================================================
class Formularios(models.Model):
    consulta = models.ForeignKey(Consultas, on_delete=models.CASCADE, related_name="formularios_evolucao")
    titulo = models.CharField(max_length=150, default="Anamnese / Evolução de Caso")
    conteudo_clinico = models.TextField(verbose_name="Prontuário/Anotações da Sessão")
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Formulário {self.id} - Consulta: {self.consulta.id}"


# ==============================================================================
# REF09 & REF10: GERENCIAR CHATS / MENSAGEM
# ==============================================================================
class Chats(models.Model):
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="chats_paciente", limit_choices_to={'is_psicologo': False})
    terapeuta = models.ForeignKey(Terapeuta, on_delete=models.CASCADE, related_name="chats_terapeuta")
    criado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Chat {self.id} - {self.paciente.username} & {self.terapeuta.usuario.username}"

class Mensagem(models.Model):
    chat = models.ForeignKey(Chats, on_delete=models.CASCADE, related_name="mensagens")
    remetente = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    conteudo = models.TextField()
    criado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Msg {self.id} por {self.remetente.username}"


# ==============================================================================
# REF11: GERENCIAR FEEDBACK / AVALIAÇÃO
# ==============================================================================
class FeedbackAvaliacao(models.Model):
    consulta = models.OneToOneField(Consultas, on_delete=models.CASCADE, related_name="feedback")
    nota_atendimento = models.PositiveSmallIntegerField(help_text="Nota de 1 a 5 para a sessão", default=5)
    comentario_paciente = models.TextField(blank=True, null=True)
    enviado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Feedback da Consulta {self.consulta.id} - Nota: {self.nota_atendimento}"


# ==============================================================================
# REF12: GERENCIAR RELATÓRIOS
# ==============================================================================
class Relatorios(models.Model):
    terapeuta = models.ForeignKey(Terapeuta, on_delete=models.CASCADE, related_name="relatorios_gerados")
    titulo = models.CharField(max_length=200)
    descricao_geral = models.TextField(help_text="Resumos estatísticos, horas de estágio acumuladas, etc.")
    arquivo_pdf = models.FileField(upload_to="relatorios/", blank=True, null=True)
    gerado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Relatório {self.id} - {self.titulo} por {self.terapeuta.usuario.username}"