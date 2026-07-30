from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect


class TenantRequiredMixin:
    """Recusa acesso quando não há tenant resolvido na request (ex.: acessando
    uma tela de negócio pelo domínio administrativo sem impersonação ativa).

    Exceção: um Super Admin autenticado, mas sem impersonação ativa, é
    redirecionado pro Painel do Super Admin em vez de tomar 404 — ele
    literalmente não tem nenhuma empresa "dele" pra ver aqui, mas tem um
    lugar certo pra ir; só usuários sem esse vínculo tomam o 404 de fato.
    """

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "tenant", None) is None:
            if request.user.is_authenticated and request.user.is_platform_admin:
                return redirect("platform_admin:tenant_list")
            raise Http404("Esta página só existe no contexto de uma empresa.")
        return super().dispatch(request, *args, **kwargs)


class AdminEmpresaRequiredMixin(TenantRequiredMixin):
    """Restringe a view ao papel admin_empresa dentro do tenant atual --
    usado pelas telas de Configurações (Usuários/Empresa/Aparência), que
    mexem em algo que afeta a empresa inteira, não só o usuário logado.

    Herda a checagem de tenant do TenantRequiredMixin (via super().dispatch());
    se essa checagem redirecionar/404, curto-circuita antes de olhar o papel.
    """

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "tenant", None) is None:
            return super().dispatch(request, *args, **kwargs)

        from apps.accounts.models import Membership

        is_admin = Membership.objects.filter(
            tenant=request.tenant,
            user=request.user,
            role=Membership.Role.ADMIN_EMPRESA,
            is_active=True,
        ).exists()
        if not is_admin:
            messages.error(request, "Só administradores da empresa acessam essa página.")
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)


class HtmxTemplateMixin:
    """Renderiza `partial_template_name` em requests HTMX (ex.: busca ao vivo
    recarregando só a tabela) e `template_name` no load normal da página.
    Reaproveitado por clients/staff/services — mesmo padrão de lista com
    busca instantânea sem recarregar a página inteira."""

    partial_template_name = None

    def get_template_names(self):
        if self.request.htmx and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()
