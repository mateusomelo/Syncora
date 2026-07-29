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
