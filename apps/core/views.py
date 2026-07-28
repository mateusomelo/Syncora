from django.http import Http404


class TenantRequiredMixin:
    """Recusa acesso quando não há tenant resolvido na request (ex.: acessando
    uma tela de negócio pelo domínio administrativo sem impersonação ativa).
    """

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "tenant", None) is None:
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
