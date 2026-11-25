from common import *
import hashlib
if (STATE/'.migration_completed').exists():raise RuntimeError('Refusing to back up legacy after successful migration')
if not (STATE/'seed-manifest.json').exists():raise RuntimeError('Create legacy data before migration')
# Останавливаем запись до снимка; MySQL остаётся доступной для dump и pgloader.
run(['docker','stop','mattermost'],check=False)
compose('legacy','up','-d','--wait','--wait-timeout','180','db-mysql')
backup=STATE/'backups'/os.environ.get('GITHUB_RUN_ID',str(int(time.time())))
backup.mkdir(parents=True,exist_ok=True);backup.chmod(0o700)
command='export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; exec mysqldump -uroot --single-transaction --routines --triggers --events --no-tablespaces --set-gtid-purged=OFF mattermost'
dump=run(['docker','exec','mattermost-mysql','sh','-c',command],capture=True)
if not dump or 'CREATE TABLE' not in dump:raise RuntimeError('Empty or invalid SQL backup')
file=backup/'mysql.sql';file.write_text(dump);file.chmod(0o600)
run(['docker','run','--rm','--user','0','-v','mattermost_practice_data:/source:ro','-v',str(backup)+':/backup','postgres:15-alpine','sh','-c','tar -czf /backup/mattermost-data.tar.gz -C /source .'])
counts_sql='SELECT (SELECT COUNT(*) FROM Users),(SELECT COUNT(*) FROM Teams),(SELECT COUNT(*) FROM Channels),(SELECT COUNT(*) FROM Posts),(SELECT COUNT(*) FROM FileInfo);'
counts=run(['docker','exec','mattermost-mysql','sh','-c','export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; exec mysql -uroot -N mattermost -e "$1"','sh',counts_sql],capture=True).strip().split('\t')
summary={'tables':dict(zip(['users','teams','channels','posts','fileinfo'],map(int,counts))),'mysql_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'files_sha256':hashlib.sha256((backup/'mattermost-data.tar.gz').read_bytes()).hexdigest(),'backup_id':backup.name}
(STATE/'source-counts.json').write_text(json.dumps(summary,indent=2))
(ARTIFACTS/'backup-summary.json').write_text(json.dumps(summary,indent=2))
print('Consistent MySQL dump and file backup saved outside Git and downloadable artifacts')
