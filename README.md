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

### Tasks periódicas (Celery worker + beat)

Lembretes de agendamento, aniversário, retorno e a sincronização de calendário externo (`apps.calendar_sync.tasks.sync_all_calendars`, a cada 15 min) só rodam com um worker **e** um beat ativos — nenhum dos dois inicia sozinho com `runserver`. Precisa do Redis rodando (ver seção de ambiente local acima). Em dois terminais separados:

```powershell
.\.venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info --pool=solo   # --pool=solo é obrigatório no Windows
```

```powershell
.\.venv\Scripts\Activate.ps1
celery -A config beat --loglevel=info
```

Para disparar uma sincronização de calendário manualmente (sem esperar os 15 min), sem precisar do beat:

```python
from apps.calendar_sync.tasks import sync_all_calendars
sync_all_calendars.delay()
```

## Multi-tenant

Toda request passa pelo `TenantResolutionMiddleware` (`apps/tenants/middleware.py`), que resolve o tenant pelo `Host` header (subdomínio `empresa.<TENANT_BASE_DOMAIN>` ou domínio próprio verificado) e popula o contextvar usado pelos managers (`apps/core/models.py`). Em desenvolvimento local, `localhost`/`127.0.0.1` (variável `TENANT_BYPASS_HOSTS`) pulam a resolução de tenant — é assim que `/admin/` funciona sem precisar configurar um subdomínio real. Esse atalho fica vazio em produção.

## Estrutura

Ver a árvore completa e a responsabilidade de cada app em `docs/architecture/00-arquitetura-aprovada.md`. Implementado e testado até agora (fases 1–10 do plano): `core`, `tenants`, `accounts`, `authentication`, `audit`, `platform_admin`, `branding`, `clients`, `staff`, `services`, `scheduling`, `finance`, `reports`, `dashboard`, `notifications`, `calendar_sync`, `verticals/registry` + `verticals/barber|dentistry|psychology`. Restam: hardening de produção e preparação de lançamento (fases 11–12).

### Módulos verticais (`apps/verticals/*`)

Habilitados por empresa via FeatureFlag (`barbearia`, `odontograma`, `psicologia` — painel do Super Admin). `apps/verticals/registry.py` decide quais estão ativos e o `VerticalRequiredMixin` bloqueia (404) acesso direto a uma URL de um módulo desativado, não só esconde o menu.

- **Barbearia**: pacotes de sessões (com controle de sessões restantes por cliente), produtos, e um fluxo de caixa (abrir/fechar/movimentar).
- **Odontologia**: prontuário unificado por paciente — odontograma (32 dentes, notação FDI), anamnese, tratamentos, receitas, atestados e orçamentos com parcelamento automático.
- **Psicologia**: prontuário com controle de acesso reforçado (LGPD) — **nem admin da empresa nem Super Admin veem o conteúdo clínico por padrão**, só o profissional responsável ou quem recebeu concessão explícita. Ver `apps/verticals/psychology/models.py:ClinicalRecord.user_has_access()`.

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

## Deploy em produção

Arquitetura de hospedagem adotada:

- **Railway** — o Django inteiro (templates, API, admin, tudo) roda aqui, como 3 serviços a partir do mesmo repositório: `web` (gunicorn), `worker` (Celery) e `beat` (Celery beat), todos definidos no `Procfile` da raiz. Também hospeda o addon de **PostgreSQL** e o addon de **Redis**.
- **Netlify** — hospeda só o site estático institucional (`netlify-site/`, pasta separada, sem nenhuma lógica de negócio), no domínio apex (ex.: `syncora.app`). O botão "Criar minha empresa" desse site aponta para o cadastro real, servido pelo Django no Railway.

Por causa disso, a divisão de domínio fica assim:

| Domínio | Aponta para | Serve |
|---|---|---|
| `syncora.app` (apex) | Netlify | Site institucional estático |
| `app.syncora.app` | Railway | Cadastro self-service (`MARKETING_HOST`) |
| `admin.syncora.app` | Railway | Painel do Super Admin |
| `connect.syncora.app` | Railway | Callback fixo do OAuth de calendário |
| `*.syncora.app` (wildcard) | Railway | Subdomínio de cada empresa cliente |

O apex e o wildcard são registros DNS independentes — não há conflito em apontar um pro Netlify e o outro pro Railway.

### Passo a passo: Railway (backend Django + Postgres + Redis)

1. **Criar o projeto**: no [Railway](https://railway.app), "New Project" → "Deploy from GitHub repo" → selecione este repositório.
2. **Adicionar o Postgres**: dentro do projeto, "New" → "Database" → "Add PostgreSQL". O Railway injeta `DATABASE_URL` automaticamente nas variáveis do projeto — não precisa criar essa variável à mão (ver `config/settings/base.py`, que já prioriza `DATABASE_URL` quando ela existe).
3. **Adicionar o Redis**: "New" → "Database" → "Add Redis". Injeta `REDIS_URL` automaticamente, do mesmo jeito.
4. **Criar os 3 serviços a partir do mesmo repo** (o Railway lê o `Procfile` da raiz e permite escolher qual processo cada serviço roda):
   - Serviço `web`: process type `web` — vai expor a porta HTTP pública. Ative "Generate Domain" pra ter uma URL `*.up.railway.app` de teste antes do domínio próprio estar pronto.
   - Serviço `worker`: process type `worker` (Celery) — sem porta pública.
   - Serviço `beat`: process type `beat` (Celery beat) — sem porta pública. **Só rode uma instância** (beat duplicado dispara tasks repetidas).
   
   Os 3 serviços precisam das mesmas variáveis de ambiente (Railway deixa compartilhar variáveis entre serviços do mesmo projeto).
5. **Configurar as variáveis de ambiente** (ver lista completa mais abaixo) em cada um dos 3 serviços.
6. **Domínio próprio**: no serviço `web` → Settings → Networking → "Custom Domain" → adicione `app.syncora.app`, `admin.syncora.app`, `connect.syncora.app` e o wildcard `*.syncora.app`, criando os registros CNAME correspondentes no seu provedor de DNS apontando pro valor que o Railway mostrar.
7. **Migrations e arquivos estáticos**: diferente do Heroku, o Railway **não** roda uma linha `release:` do Procfile automaticamente. No serviço `web` → Settings → Deploy → **Pre-Deploy Command**, configure:
   ```
   python manage.py migrate --noinput && python manage.py collectstatic --noinput
   ```
   Isso roda uma vez antes de cada deploy do `web` (não precisa repetir nos serviços `worker`/`beat`).

### Passo a passo: Netlify (site estático)

1. No [Netlify](https://app.netlify.com), "Add new site" → "Import an existing project" → selecione este mesmo repositório.
2. O `netlify.toml` na raiz já configura tudo: `publish = "netlify-site"`, sem comando de build (é HTML puro, sem etapa de compilação).
3. Domínio: em Site settings → Domain management, adicione `syncora.app` (apex) como domínio primário e siga as instruções de DNS do Netlify (geralmente um registro `A`/`ALIAS` pro apex).
4. Pronto — qualquer alteração em `netlify-site/` publicada na branch principal já entra em produção automaticamente.

### Conectando o PostgreSQL

Não precisa de nenhum passo manual de conexão — o addon do Railway já injeta `DATABASE_URL` no ambiente de todos os serviços do projeto automaticamente. Se precisar rodar uma migration ou abrir um shell manualmente contra o banco de produção:

```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py dbshell
```

(`railway run` executa o comando localmente já com as variáveis de ambiente do serviço selecionado, incluindo `DATABASE_URL` — requer a [Railway CLI](https://docs.railway.app/guides/cli) instalada e `railway login`/`railway link` feitos antes.)

### Variáveis de ambiente — lista completa

Todas documentadas com comentário em `.env.example`; resumo por categoria:

| Variável | Obrigatória? | Observação |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Sim | `config.settings.production` no Railway |
| `SECRET_KEY` | Sim | gere uma única, nunca reaproveite a de dev |
| `DEBUG` | Sim | `False` em produção |
| `ALLOWED_HOSTS` | Sim | `syncora.app,.syncora.app` |
| `DATABASE_URL` | Auto (Railway) | injetada pelo addon de Postgres |
| `REDIS_URL` | Auto (Railway) | injetada pelo addon de Redis |
| `RAILWAY_PUBLIC_DOMAIN` | Auto (Railway) | não precisa definir manualmente |
| `FIELD_ENCRYPTION_KEY` | Sim | gere com o comando no `.env.example` — diferente do `SECRET_KEY` |
| `PLATFORM_ADMIN_HOST` | Sim | `admin.syncora.app` |
| `TENANT_BASE_DOMAIN` | Sim | `syncora.app` |
| `MARKETING_HOST` | Sim | `app.syncora.app` |
| `CALENDAR_SYNC_HOST` | Sim | `connect.syncora.app` |
| `CALENDAR_SYNC_CALLBACK_BASE_URL` | Sim | `https://connect.syncora.app` |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | Sim | provedor SMTP real (SES, Postmark, Resend, etc.) |
| `DEFAULT_FROM_EMAIL` | Não | tem default |
| `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` | Não | em branco = botão aparece desabilitado, ver seção de calendário |
| `MICROSOFT_OAUTH_CLIENT_ID` / `MICROSOFT_OAUTH_CLIENT_SECRET` | Não | idem |
| `SENTRY_DSN` | Não | em branco = sem monitoramento de erro, app funciona normal |
| `SENTRY_TRACES_SAMPLE_RATE` / `ENVIRONMENT` | Não | têm default |
| `AWS_STORAGE_BUCKET_NAME` | Não | em branco = mídia fica em disco local (não recomendado em produção) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_S3_REGION_NAME` / `AWS_S3_ENDPOINT_URL` / `AWS_S3_CUSTOM_DOMAIN` | Só se usar S3 | AWS S3, Cloudflare R2 ou Backblaze B2 — todos compatíveis |

### Checklist final antes de lançar

- [ ] `SECRET_KEY` e `FIELD_ENCRYPTION_KEY` gerados de novo pra produção (nunca os mesmos do `.env` de dev)
- [ ] `DEBUG=False` confirmado no Railway
- [ ] Os 3 serviços (`web`, `worker`, `beat`) rodando, com **apenas um** `beat` ativo
- [ ] Domínios configurados: apex → Netlify, `app.`/`admin.`/`connect.`/wildcard → Railway
- [ ] Certificado HTTPS ativo em todos os domínios (Railway e Netlify emitem automaticamente via Let's Encrypt assim que o DNS propaga)
- [ ] `python manage.py createsuperuser` rodado no ambiente de produção (super admin da plataforma)
- [ ] E-mail transacional testado de verdade (recuperação de senha, boas-vindas do cadastro)
- [ ] `AWS_STORAGE_BUCKET_NAME` configurado se for lançar com clientes reais fazendo upload de foto/documento (senão o disco se perde a cada redeploy)
- [ ] `SENTRY_DSN` configurado (recomendado antes do primeiro cliente real)
- [ ] Testar o cadastro self-service de ponta a ponta em `https://app.syncora.app/cadastro/`
- [ ] Testar login num subdomínio de empresa real (não o de teste) para confirmar TLS do wildcard
- [ ] Rodar um restore de teste do backup do Postgres (ver `docs/operations/backup-restore.md`) antes do lançamento valer pra clientes de verdade
