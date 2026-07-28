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

Ver a árvore completa e a responsabilidade de cada app em `docs/architecture/00-arquitetura-aprovada.md`. Implementado até agora: `core`, `tenants`, `accounts`, `authentication`, `audit`. Os demais apps (`platform_admin`, `branding`, `clients`, `staff`, `services`, `scheduling`, `calendar_sync`, `finance`, `reports`, `notifications`, `dashboard`, `verticals/*`, `api`) estão scaffolded (pasta criada) e serão implementados nas próximas fases do plano.
