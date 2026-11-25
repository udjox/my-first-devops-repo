from common import *
import shutil
for name,args in {
 'mattermost.log':['docker','logs','--tail','200','mattermost'],
 'postgres.log':['docker','logs','--tail','100','mattermost-postgres'],
 'containers.txt':['docker','ps','-a','--format','{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'],
 'volumes.json':['docker','volume','inspect','mattermost_practice_data','mattermost_practice_postgres'],
}.items():
    result=run(args,capture=True,check=False)
    (ARTIFACTS/name).write_text(redact(result))
(ARTIFACTS/'.env').write_text(''.join(key+'=***\n' for key in KEYS))
if (STATE/'mattermost-before.png').exists(): shutil.copyfile(STATE/'mattermost-before.png',ARTIFACTS/'mattermost-before.png')
status={}
if (ARTIFACTS/'migration-status.json').exists():status=json.loads((ARTIFACTS/'migration-status.json').read_text())
verified=(ARTIFACTS/'data-verification.json').exists() and (ARTIFACTS/'browser-verification.json').exists()
summary='# Mattermost migration report\n\n'
summary+='Run: '+os.environ.get('GITHUB_RUN_ID','local')+'\n\n'
summary+='Data and browser checks: '+('PASSED' if verified else 'NOT COMPLETED')+'\n\n'
summary+='Backup and transfer skipped: '+str(status.get('already_migrated',False))+'\n\n'
summary+='Source: Mattermost 9.5.0 + MySQL 8.0\n\nTarget: Mattermost 12.0.1 + PostgreSQL 15\n\n'
summary+='Checks: original user and private channel, original message IDs and text, attachment SHA256, avatar SHA256, browser display, legacy container removal.\n\n'
summary+='Backups and migration marker are stored outside the repository in the private runner state directory. Database dump and credentials are not uploaded as public artifacts.\n'
(ARTIFACTS/'migration-report.md').write_text(summary)
# Не допускаем загрузку секрета, даже если сторонняя утилита напечатала его в лог.
for file in ARTIFACTS.rglob('*'):
    if file.is_file() and file.suffix not in ['.png','.jpg']:
        try:file.write_text(redact(file.read_text()))
        except UnicodeDecodeError:pass
print('Migration report, screenshots and redacted logs collected')
