from common import *
marker=STATE/'.migration_completed'
already=marker.exists()
if already:
    saved=json.loads(marker.read_text())
    # Флаг связан с конкретным томом PostgreSQL: потеря базы не маскируется файлом.
    compose('prod','up','-d','--wait','--wait-timeout','120','db-postgres')
    if pg_query('SELECT system_identifier FROM pg_control_system();') != saved['postgres_system_identifier']:
        raise RuntimeError('Marker belongs to a different PostgreSQL volume; do not skip migration')
    if not pg_query("SELECT to_regclass('public.posts');"):
        raise RuntimeError('Migration marker exists, but target database is missing')
if os.environ.get('GITHUB_OUTPUT'):
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('already_migrated='+str(already).lower()+'\n')
(ARTIFACTS/'migration-status.json').write_text(json.dumps({'already_migrated':already,'run_id':os.environ.get('GITHUB_RUN_ID','local'),'backup_skipped':already,'transfer_skipped':already},indent=2))
print('Migration already completed; backup and transfer will be skipped' if already else 'Initial migration required')
