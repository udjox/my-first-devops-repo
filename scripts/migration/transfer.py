from common import *
import re
if (STATE/'.migration_completed').exists():raise RuntimeError('Refusing to overwrite an already migrated database')
cfg=settings()
compose('prod','up','-d','--wait','--wait-timeout','180','db-postgres')
# Каждая незавершённая попытка начинает с чистой целевой схемы. Исходный том MySQL сохраняется.
pg_query('DROP SCHEMA IF EXISTS mattermost CASCADE; DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION mmuser;')
mysql='root:'+cfg['DB_MYSQL_ROOT_PASSWORD']+'@tcp(db-mysql:3306)/mattermost'
postgres='postgres://mmuser:'+cfg['DB_POSTGRES_PASSWORD']+'@db-postgres:5432/mattermost?sslmode=disable'
def tool(*args, log=None):
    return run(['docker','run','--rm','--platform','linux/amd64','--network','mattermost_practice_network','--entrypoint','/usr/local/bin/migration-assist','mattermost-practice-tools:0.8',*args],capture=True,log=log)
print('Checking source MySQL schema',flush=True)
tool('mysql',mysql,'--fix-artifacts','--fix-unicode','--fix-varchar',log=ARTIFACTS/'mysql-preflight.log')
print('Preparing PostgreSQL schema for source Mattermost 9.5.0',flush=True)
tool('postgres',postgres,'--run-migrations','--mattermost-version','9.5.0',log=ARTIFACTS/'postgres-schema.log')
load=tool('pgloader','--mysql',mysql,'--postgres',postgres,'--remove-null-chars')
if not load.startswith('LOAD DATABASE'): raise RuntimeError('Empty pgloader configuration')
load=load.replace('WITH data only,','WITH include drop, data only,')
load=load.replace('workers = 8','workers = 2').replace('prefetch rows = 10000','prefetch rows = 1000')
# Идемпотентный сброс схемы выше дополняет include drop. data only сохраняет типы и структуру официальных миграций.
path=STATE/'migration.load';path.write_text(load);path.chmod(0o600)
print('Transferring source data using official Mattermost pgloader',flush=True)
result=run(['docker','run','--rm','--platform','linux/amd64','--network','mattermost_practice_network','-v',str(path)+':/migration.load:ro','--entrypoint','pgloader','mattermost-practice-tools:0.8','/migration.load'],capture=True,log=ARTIFACTS/'pgloader.log')
if re.search(r'\b(ERROR|FATAL)\b',(ARTIFACTS/'pgloader.log').read_text()):raise RuntimeError('pgloader reported errors; inspect redacted artifact log')
source=json.loads((STATE/'source-counts.json').read_text())
for table,expected in source['tables'].items():
    if int(pg_query('SELECT COUNT(*) FROM '+table+';')) != expected: raise RuntimeError('Transferred row count mismatch: '+table)
tool('postgres','post-migrate','--create-indexes',postgres,log=ARTIFACTS/'postgres-indexes.log')
(ARTIFACTS/'transfer.json').write_text(json.dumps({'source':'MySQL 8.0','target':'PostgreSQL 15','source_schema_version':'9.5.0','include_drop':True,'clean_schema_on_retry':True,'completed':True},indent=2))
path.unlink(missing_ok=True)
print('Database transfer finished; application upgrade will run next',flush=True)
