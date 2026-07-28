# Syncora — Arquitetura e Plano de Implementação

## Contexto

O Syncora é um SaaS White Label multi-tenant de agendamento e gestão empresarial (barbearias, clínicas odontológicas, psicólogos, com arquitetura modular para novos segmentos), especificado em 4 partes de documentação pelo cliente. O pedido explícito da Parte 1 é que, antes de qualquer código, seja apresentada a arquitetura completa (apps, banco, multi-tenant, auth, fases) para aprovação. Este documento é essa apresentação. Projeto greenfield — será criado em `C:\Users\Matteus\Projects\syncora` (confirmado pelo usuário).

Duas decisões técnicas precisavam de resolução por não estarem 100% especificadas ou por conflito interno no documento — estão resolvidas abaixo com justificativa, conforme pedido explícito do cliente ("caso alguma decisão técnica possa ser melhorada, explique o motivo antes de implementá-la").

---

## Decisões técnicas resolvidas

### 1. Conflito Framer Motion vs stack Django/HTMX
A Parte 2 pede Framer Motion (lib React), mas a Parte 1 fixa o frontend como templates Django + Tailwind + HTMX + JS ES6, sem SPA/React — incompatível.

**Decisão:** Alpine.js (interatividade declarativa leve: dropdowns, abas, estado de modal/drawer — parceiro natural do HTMX, mesma filosofia de atributos em HTML server-rendered) + Motion One (animações imperativas de entrada/saída, easing, stagger — wrapper fino sobre a Web Animations API nativa, ~4kb, sensação mais próxima do Framer Motion sem exigir React) + GSAP só para coreografias complexas (drag do kanban/calendário) + CSS transitions/HTMX swap transitions para micro-interações triviais. Preserva o efeito "fluidez premium" pedido sem violar a stack.

### 2. Estratégia multi-tenant: shared schema (não schema-per-tenant)
Meta é "milhares de empresas simultaneamente" + domínio próprio por empresa + Super Admin precisa de analytics cross-tenant.

**Decisão:** single database Postgres, `tenant_id` em todo model tenant-scoped, isolamento em 4 camadas:
1. Abstract model `TenantModel` (FK `tenant` obrigatória) + `TenantManager` que filtra automaticamente pelo tenant corrente (lido de um `contextvar`, seguro em sync/async).
2. `TenantResolutionMiddleware` resolve o tenant pelo `Host` header (subdomínio ou domínio próprio) e injeta em `request.tenant` + contextvar, antes da autenticação.
3. **Postgres Row-Level Security como hardening extra**: `SET LOCAL app.current_tenant_id` por request/transação + políticas RLS em todas as tabelas tenant-scoped — rede de segurança mesmo contra bug de código que esqueça o filtro.
4. Testes automatizados de isolamento (2 tenants fixture, todo endpoint garante que A nunca vê dado de B).

Rejeitado schema-per-tenant (django-tenants): em escala de milhares de tenants, migrações por schema ficam lentas/arriscadas, `search_path` por conexão quebra connection pooling em modo transaction (essencial nessa escala), e analytics cross-tenant do Super Admin exigiria iterar schemas ou FDW. Shared schema resolve os três problemas com uma migração atômica e queries diretas, ao custo de exigir disciplina de filtro — mitigada pelas 4 camadas acima.

**Domínio personalizado:** `Tenant.subdomain` (→ `empresa.syncora.app`, wildcard DNS + certificado wildcard) e model `CustomDomain` (domínio próprio tipo `agenda.empresa.com.br`, com verificação via registro TXT e TLS on-demand via Caddy/Traefik). `TenantResolutionMiddleware` faz lookup por host: subdomínio primeiro (sem DB), depois `CustomDomain` cacheado em Redis (TTL curto, invalidado ao alterar). Super Admin acessa por domínio administrativo separado (`admin.syncora.app`), fora do middleware de tenant.

### 3. Tempo real: SSE + Redis pub/sub (não Django Channels)
A necessidade real é push unidirecional ("algo mudou, revalide a tela") — a escrita já é POST/HTMX normal; não há colaboração bidirecional de baixa latência.

**Decisão:** Server-Sent Events (endpoint async, `django-eventstream` ou equivalente) + Redis pub/sub por canal `tenant:{id}:agenda`. Ao criar/editar/cancelar `Appointment`, publica-se evento leve (tipo+id+ação); páginas de agenda abertas mantêm conexão SSE e, ao receber evento, disparam `hx-get` via HTMX para revalidar só o slot afetado (out-of-band swap) — autorização é revalidada no refetch normal, sem dado sensível no payload do evento. Django roda sob ASGI (uvicorn), atendendo views normais e o streaming no mesmo processo. Redis já é necessário como broker do Celery, reaproveitado. Channels fica como opção futura incremental só se surgir necessidade genuinamente bidirecional (não é o caso hoje).

---

## Apps Django

**Plataforma/core:**
- `core` — abstract models (`TenantModel`, `TimeStampedModel`, `SoftDeleteModel`), exceptions, resposta padronizada de API, paginação, permissions base, contextvar de tenant.
- `tenants` — `Tenant`, `CustomDomain`, `Plan`, `FeatureFlag`, `TenantSubscription`, `Coupon` + middleware de resolução.
- `accounts` — `User` customizado, `Membership` (user↔tenant↔role), `Role`.
- `authentication` — login/logout web (sessão), JWT/refresh (SimpleJWT), reset de senha, sessões, impersonação.
- `platform_admin` — CRUD de empresas, ativação/suspensão/inadimplência, planos/limites, feature flags por empresa, estatísticas, logs, broadcast, cupons.
- `audit` — `AuditLog` genérico + `ImpersonationSession` (usado por toda a plataforma, não só white-label).
- `branding` — white-label completo (cores, logos, tema, login customizado).

**Negócio core:**
- `clients`, `staff`, `services` — CRUDs base.
- `scheduling` — Agenda Principal: `Appointment`, `Block`, `Room`, `Unit`, `WaitList`, motor de conflito, sugestões inteligentes, canal SSE.
- `calendar_sync` — integração plugável Google/Outlook/Apple, OAuth por profissional.
- `finance` — receitas, despesas, comissões, formas de pagamento.
- `reports` — motor de relatórios + exportação PDF/Excel.
- `notifications` — abstração de canais (Email/SMS/WhatsApp), templates, Celery beat.
- `dashboard` — agregações dos widgets.
- `api` — config DRF compartilhada (versionamento, OpenAPI/Swagger, exception handler global); cada app mantém seu próprio `api/` interno.

**Verticais (plugáveis por feature flag, não por `INSTALLED_APPS` dinâmico):**
- `verticals.registry` — interfaces base + serviço que consulta `FeatureFlag` do tenant para decidir menu/urls/permissões visíveis em runtime.
- `verticals.barber`, `verticals.psychology`, `verticals.dentistry` — apps independentes.
- Regra de acoplamento: core nunca importa `verticals.*`; vertical→core é FK/OneToOne explícita (não GenericForeignKey — alvo é conhecido e finito, FK dá integridade e índice); core→vertical só via Django signals (`appointment_completed`, `client_created`), que o vertical escuta.

---

## Estrutura de pastas

Raiz: `C:\Users\Matteus\Projects\syncora`

```
syncora/
├── manage.py
├── pyproject.toml
├── requirements/{base,local,staging,production,test}.txt
├── .env.example
├── docker/{django,nginx-ou-caddy}/Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── config/
│   ├── asgi.py            # uvicorn — necessário p/ SSE
│   ├── wsgi.py
│   ├── urls.py
│   ├── celery.py
│   └── settings/{base,local,staging,production,test}.py
├── apps/
│   ├── core/  ├── tenants/  ├── accounts/  ├── authentication/
│   ├── platform_admin/  ├── audit/  ├── branding/
│   ├── clients/  ├── staff/  ├── services/
│   ├── scheduling/  ├── calendar_sync/  ├── finance/
│   ├── reports/  ├── notifications/  ├── dashboard/
│   ├── verticals/{registry.py, barber/, psychology/, dentistry/}
│   └── api/
├── templates/
│   ├── base.html  ├── layouts/
│   ├── components/   # design system: button, input, select, modal, drawer, toast, skeleton, badge, card, table, kanban, timeline
│   ├── auth/  ├── dashboard/  ├── scheduling/  ├── emails/
├── static/
│   ├── src/           # Tailwind input, Alpine components, JS ES6, tailwind.config.js, package.json
│   └── dist/          # build (gitignored)
├── locale/             # pt-BR, en, es
├── media/              # gitignored / S3 em produção
└── docs/architecture/
```

---

## Modelagem de dados (por domínio)

**Tenant/Auth:** `Plan`(name, slug, max_users, max_professionals, max_appointments_month, price) · `Tenant`(name, subdomain, cnpj, status, plan FK) · `CustomDomain`(tenant FK, domain, is_primary, verified_at, ssl_status) · `FeatureFlag`(tenant FK, key, enabled) · `TenantSubscription`(tenant FK, plan FK, status, period, gateway_ref) · `Coupon` · `User`(email login, is_superadmin) · `Membership`(user FK, tenant FK, role, is_active) · `Role`.

**Agenda:** `Unit`(tenant FK, name, address) · `Room`(unit FK, name) · `Appointment`(tenant FK, client FK, professional FK, service FK, room FK null, unit FK, start_at, end_at, status, origin[syncora|google|outlook|apple], cancellation_reason) · `Block`(tenant FK, professional/room FK null, start_at/end_at, type[almoco|ferias|folga|evento|reuniao|data_comemorativa], recurrence_rule) · `WaitList`(tenant FK, client FK, desired_service/professional, desired_window, status, priority).

**Clientes/Staff/Serviços:** `Client`(tenant FK, name, phone, email, birth_date, notes, photo) + `ClientDocument` · `Professional`(tenant FK, user FK null, commission_rate, photo, status) + `WorkingHours` + `Vacation` · `ServiceCategory` · `Service`(tenant FK, category FK, name, price, duration_minutes, color, allowed_professionals M2M).

**Financeiro:** `Revenue`(tenant FK, appointment FK null, amount, payment_method, received_at) · `Expense`(tenant FK, category, amount, due_date, paid_at) · `Commission`(tenant FK, professional FK, appointment FK, amount, percentage, paid).

**White-label:** `BrandingSettings`(tenant FK OneToOne, logo, logo_dark, favicon, cores granulares, chart_colors json, theme_mode, login_bg_image, login_message, show_powered_by) — alterações auditadas via `AuditLog` genérico.

**Auditoria (plataforma inteira):** `AuditLog`(tenant FK null, actor FK, action, target_model, target_id, changes json, ip, user_agent, is_impersonated) · `ImpersonationSession`(super_admin FK, tenant FK, started_at, ended_at, reason).

**Calendar sync:** `CalendarConnection`(professional FK, provider, oauth_tokens encrypted, sync_direction, external_calendar_id, last_synced_at) · `ExternalEventMapping`(connection FK, appointment FK null, external_event_id, source_color).

**Verticais:** Barbearia → `Package`, `Product`, `CashRegisterSession`. Psicologia → `ClinicalRecord`(client OneToOne, restricted_access), `SessionNote`(clinical_record FK, appointment OneToOne null, is_confidential) — acesso restrito ao profissional designado + admin com concessão explícita (LGPD). Odontologia → `Odontogram` → `OdontogramTooth`, `Anamnesis`, `Treatment`, `Prescription`, `MedicalCertificate`, `Budget` → `Installment`.

Todo model tenant-scoped herda `TenantModel` + `TimeStampedModel`/`SoftDeleteModel`.

---

## Fluxos de autenticação

- **Web (sessão):** `django.contrib.auth` + backend customizado validando `Membership` ativa para o tenant resolvido pelo host (senha correta não basta sem vínculo ativo). Login usa `BrandingSettings` do tenant. Rate limit/lockout (django-axes), CSRF padrão.
- **API (JWT):** `djangorestframework-simplejwt` — access curto (5–15min) + refresh com rotação/blacklist (7–30 dias). Claims incluem `tenant_id`/`role`; status de suspensão checado via cache curto.
- **Recuperação de senha:** `PasswordResetView` padrão, templates/emails com branding do tenant, envio assíncrono via Celery.
- **Impersonação:** `POST /platform-admin/tenants/{id}/impersonate/` cria `ImpersonationSession` auditada, preserva sessão original do super admin (banner "Atuando como suporte em {empresa} — Sair"), toda ação grava `AuditLog` com `is_impersonated=True`, expira por timeout de segurança (também logado).

---

## Plano de fases

1. **Fundações** — scaffold, settings split, docker-compose (Postgres+Redis), CI, app `core`.
2. **Multi-tenant + Auth** — `tenants` + middleware + RLS, `accounts`/`authentication`, `audit` (base para o resto).
3. **Platform Admin MVP** — CRUD de empresas, planos/limites, feature flags, impersonação (necessário cedo para suporte/QA durante todo o desenvolvimento seguinte).
4. **White-label + Design System** — `BrandingSettings`, CSS variables dinâmicas, login customizado, i18n (pt-BR/en/es), biblioteca de componentes (Tailwind + Alpine.js + Motion One).
5. **CRUDs de negócio base** — `clients`, `staff`, `services` (estabelece o padrão list/create/edit/soft-delete + partials HTMX + viewsets DRF reaproveitado depois).
6. **Agenda (núcleo do produto)** — `scheduling`: CRUD → detecção de conflito → drag-and-drop/resize → tempo real (SSE+Redis) → lista de espera → sugestões inteligentes. Maior fase, subdividida em etapas próprias.
7. **Financeiro + Relatórios + Dashboard** — receitas/despesas/comissões, exportação PDF/Excel, widgets do dashboard.
8. **Notificações plugáveis** — interface `NotificationChannel`, Email primeiro, stubs SMS/WhatsApp atrás de feature flag, Celery beat para lembretes/aniversário/retorno.
9. **Sincronização de calendário externo** — OAuth por profissional, Google primeiro, depois Outlook/Apple na mesma interface.
10. **Módulos verticais** — Barbearia → Odontologia → Psicologia (por último, exige revisão de segurança/LGPD mais rigorosa por dado clínico sensível).
11. **Hardening e escala** — rate limiting/throttling por plano, Swagger definitivo, testes de carga (PgBouncer, índices), PWA, Spotlight search, command palette.
12. **Preparação de lançamento** — assinaturas online/cupons, onboarding automatizado de tenant, observabilidade (Sentry, logs estruturados), runbook de backup/DR.

---

## Verificação

- `docker compose up` sobe Postgres + Redis + app; `python manage.py migrate` aplica schema único.
- Criar 2 tenants via Super Admin/admin do Django e confirmar isolamento: usuário do tenant A nunca lista/edita registros do tenant B (testado via pytest com fixture de 2 tenants, e manualmente via 2 subdomínios locais em `/etc/hosts` ou `hosts` do Windows).
- Testar detecção de conflito: criar 2 agendamentos sobrepostos para o mesmo profissional/sala → deve bloquear com motivo explícito.
- Abrir a agenda em duas abas/sessões distintas do mesmo tenant, criar um agendamento em uma, confirmar atualização automática na outra via SSE sem reload.
- `/api/schema/swagger-ui/` acessível e completo (DRF spectacular ou drf-yasg).
- Rodar `pytest` (suíte cobrindo isolamento multi-tenant, auth, conflito de agenda) antes de considerar cada fase concluída.
