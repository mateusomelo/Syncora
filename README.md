# Syncora

SaaS multi-tenant de agendamento e gestão empresarial (barbearias, clínicas odontológicas, psicólogos), White Label, preparado para escalar a milhares de empresas.

A arquitetura completa (decisões de multi-tenant, apps, modelagem de dados, fluxos de auth e plano de fases) está documentada em [`docs/architecture/00-arquitetura-aprovada.md`](docs/architecture/00-arquitetura-aprovada.md) — leia esse documento antes de mexer em qualquer coisa aqui.

## Stack

Python 3.12+ · Django 5.2 · Django REST Framework · PostgreSQL 17 · Redis · Tailwind CSS + HTMX + Alpine.js (sem SPA/React).

## Ambiente de desenvolvimento local (Windows, sem Docker)

Este ambiente foi montado com **PostgreSQL e Redis nativos via [Scoop](https://scoop.sh/)** (sem precisar de admin/Docker Desktop), porque a máquina de desenvolvimento não tinha Docker instalado. Em produção/CI, use `docker-compose.yml` normalmente.

Serviços instalados:
- PostgreSQL 17 → `%USERPROFILE%\scoop\apps\postgresql17\current` (dados em `...\current\data`)
- Redis → `%USERPROFILE%\scoop\apps\redis\current`

**Depois de reiniciar o Windows**, os dois processos precisam ser religados (não estão registrados como serviço do Windows):

```powershell
powershell -File "$env:USERPROFILE\.local\syncora\start-dev-services.ps1"
```

Isso sobe o Postgres em `localhost:5432` e o Redis em `localhost:6379`. A senha do papel `syncora_dev` está em `%USERPROFILE%\.local\syncora\db_dev_password.txt` e já espelhada no `.env` do projeto.

## Rodando o projeto

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Admin do Django: http://localhost:8000/admin/
- Obter JWT: `POST /auth/api/token/` com `{"email": "...", "password": "..."}`
- Login web: http://localhost:8000/auth/login/

`config.settings.local` é o padrão do `manage.py`. Use `DJANGO_SETTINGS_MODULE=config.settings.test` para rodar a suíte (`pytest`), e `config.settings.production`/`staging` em deploy.

## Multi-tenant

Toda request passa pelo `TenantResolutionMiddleware` (`apps/tenants/middleware.py`), que resolve o tenant pelo `Host` header (subdomínio `empresa.<TENANT_BASE_DOMAIN>` ou domínio próprio verificado) e popula o contextvar usado pelos managers (`apps/core/models.py`). Em desenvolvimento local, `localhost`/`127.0.0.1` (variável `TENANT_BYPASS_HOSTS`) pulam a resolução de tenant — é assim que `/admin/` funciona sem precisar configurar um subdomínio real. Esse atalho fica vazio em produção.

## Estrutura

Ver a árvore completa e a responsabilidade de cada app em `docs/architecture/00-arquitetura-aprovada.md`. Implementado e testado até agora (fases 1–9 do plano): `core`, `tenants`, `accounts`, `authentication`, `audit`, `platform_admin`, `branding`, `clients`, `staff`, `services`, `scheduling`, `finance`, `reports`, `dashboard`, `notifications`, `calendar_sync`. Restam: módulos verticais (`verticals/barber|psychology|dentistry`), hardening de produção e preparação de lançamento.

## Sincronização de calendário externo (Google/Outlook)

O app `calendar_sync` está pronto (OAuth, tokens criptografados, importação/exportação de eventos, cores por origem na agenda), mas **as credenciais são suas** — sem elas, o botão de conectar aparece e avisa que a integração não está configurada, em vez de quebrar. Para ligar de verdade:

**Google Calendar** (console.cloud.google.com):
1. Crie um projeto → ative a "Google Calendar API".
2. Tela de consentimento OAuth → tipo "Externo" (ou "Interno" se for Google Workspace).
3. Credenciais → "ID do cliente OAuth" → tipo "Aplicativo da Web".
4. Em "URIs de redirecionamento autorizados", cadastre exatamente: `{CALENDAR_SYNC_CALLBACK_BASE_URL}/calendar-sync/google/callback/` (em produção, algo como `https://connect.syncora.app/calendar-sync/google/callback/`).
5. Copie o Client ID e o Client Secret para `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` no `.env`.

**Outlook/Microsoft 365** (portal.azure.com → Azure Active Directory → App registrations):
1. Novo registro de app → tipo "Contas em qualquer diretório organizacional e contas pessoais".
2. Em "Redirect URIs" (plataforma Web), cadastre: `{CALENDAR_SYNC_CALLBACK_BASE_URL}/calendar-sync/outlook/callback/`.
3. "Certificates & secrets" → novo client secret.
4. "API permissions" → Microsoft Graph → adicione `Calendars.ReadWrite` e `offline_access`.
5. Copie Application (client) ID e o secret para `MICROSOFT_OAUTH_CLIENT_ID` / `MICROSOFT_OAUTH_CLIENT_SECRET`.

**Apple Calendar (iCloud)** ainda não está implementado — a Apple não oferece OAuth2 para apps de terceiros; o acesso real é via CalDAV com uma senha de app gerada no Apple ID, um mecanismo diferente do usado acima. Fica para uma fase futura.

`CALENDAR_SYNC_HOST` é um domínio fixo e separado (não o subdomínio de cada empresa) porque Google/Microsoft exigem um redirect_uri idêntico a cada chamada — não dá pra cadastrar o subdomínio de cada cliente. Em produção, aponte um subdomínio real (ex.: `connect.syncora.app`) pra essa variável e cadastre-o nos consoles acima; em desenvolvimento local já vem configurado como `connect.localhost`.
