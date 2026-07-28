# Backup e Recuperação de Desastres (DR)

Este runbook cobre o banco de dados de produção do Syncora (Postgres,
schema compartilhado com `tenant_id` — ver `docs/architecture/00-arquitetura-aprovada.md`).
Como todas as empresas vivem no mesmo banco, o backup é único para a
plataforma inteira; não existe "backup por empresa" separado.

## O que precisa de backup

1. **PostgreSQL** (crítico) — todos os dados de todas as empresas.
2. **Media files** (`MEDIA_ROOT` / bucket S3 em produção) — logos, fotos,
   documentos de clientes, anexos de prontuário. Se estiver em S3,
   versionamento do bucket já cobre a maior parte do risco.
3. **Segredos** (`.env` de produção) — guardados num cofre (Secrets
   Manager / Vault), nunca no mesmo lugar do backup do banco.
4. Redis **não** precisa de backup — é cache e broker de fila
   (Celery), reconstruível a partir do Postgres a qualquer momento.

## Estratégia de backup do Postgres

Dois mecanismos combinados:

- **Dump lógico diário** (`pg_dump -Fc`), retido por 30 dias, para
  restauração seletiva rápida e para testes de restore.
- **WAL archiving contínuo** (`archive_mode = on` + `wal_level =
  replica`, arquivado para S3/similar) para recuperação **point-in-time**
  (restaurar para "5 minutos antes do incidente", não só "a última
  meia-noite").

```bash
# Dump diário (rodar via cron/Celery beat, fora do horário de pico)
pg_dump -Fc --no-owner --dbname="$DATABASE_URL" -f "syncora_$(date +%Y%m%d).dump"

# Enviar para armazenamento fora do servidor do banco (S3, outro provedor)
aws s3 cp "syncora_$(date +%Y%m%d).dump" s3://syncora-backups/postgres/
```

Se o provedor de banco gerenciado (RDS, Cloud SQL, Neon, etc.) já
oferece snapshots automáticos + PITR nativos, prefira usar o mecanismo
gerenciado em vez de reinventar isso na aplicação — o `pg_dump` diário
continua valendo como segunda camada independente do provedor.

## Metas (ajustar com o negócio antes do lançamento)

| Métrica | Meta inicial sugerida |
|---|---|
| RPO (perda de dados aceitável) | 5 minutos (via WAL/PITR) |
| RTO (tempo até religar) | 1 hora para restaurar o banco completo |
| Retenção de dumps diários | 30 dias |
| Retenção de WAL | 7 dias (suficiente pra PITR de incidentes recentes) |

## Procedimento de restore

**Restore completo (novo servidor / disaster recovery):**

```bash
# 1. Provisionar um Postgres novo (mesma versão major, 17.x)
# 2. Restaurar o dump mais recente
pg_restore --no-owner --clean --if-exists -d "$DATABASE_URL" syncora_20260728.dump

# 3. Rodar migrations pendentes (caso o dump seja de antes do deploy atual)
python manage.py migrate

# 4. Verificar integridade básica
python manage.py check
python manage.py shell -c "from apps.tenants.models import Tenant; print(Tenant.objects.count())"
```

**Point-in-time recovery** (ex.: reverter para o momento antes de uma
migration ruim ou uma exclusão em massa acidental): siga o mecanismo de
PITR do provedor gerenciado (todos os grandes provedores documentam
"restore to point in time" via console/CLI) apontando para o timestamp
desejado, usando o WAL archiving já configurado.

**Depois de qualquer restore:** validar login em pelo menos uma empresa
de teste, conferir `AuditLog` mais recente bate com o timestamp
esperado do restore, e só então liberar o tráfego de produção.

## Cenários de desastre

- **Exclusão acidental de dados de uma empresa**: como o soft-delete
  (`SoftDeleteModel`) já protege a maioria das exclusões via UI, o
  primeiro passo é sempre checar se o registro só está com `deleted_at`
  setado (recuperável direto, sem restore de backup) antes de escalar
  para restore de banco.
- **Migration com bug em produção**: restaurar o dump mais recente
  anterior à migration, ou usar PITR para o instante exato antes do
  deploy, depois reaplicar migrations corrigidas.
- **Perda total da região/provedor**: subir a infraestrutura em nova
  região a partir do último dump + WAL arquivado, apontar DNS
  (`*.syncora.app`, `admin.syncora.app`, `connect.syncora.app`) para o
  novo ambiente.

## Testar o restore (fazer isso de verdade, periodicamente)

Um backup nunca testado não é um backup — é uma esperança. Trimestralmente:
1. Restaurar o dump mais recente num ambiente isolado (não produção).
2. Rodar a suíte de smoke tests (ver `docs/architecture/00-arquitetura-aprovada.md`, seção de verificação) contra esse ambiente restaurado.
3. Cronometrar o processo inteiro — se passar da meta de RTO, é sinal de que o procedimento precisa de automação melhor antes que aconteça de verdade.
