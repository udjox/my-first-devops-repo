from common import *
verification=json.loads((ARTIFACTS/'data-verification.json').read_text())
browser=json.loads((ARTIFACTS/'browser-verification.json').read_text())
assert verification['passed'] and browser['passed']
marker=STATE/'.migration_completed'
if not marker.exists():
    value={'postgres_system_identifier':pg_query('SELECT system_identifier FROM pg_control_system();'),'verified_version':'12.0.1','run_id':os.environ.get('GITHUB_RUN_ID','local'),'completed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    temporary=STATE/'.migration_completed.tmp';temporary.write_text(json.dumps(value,indent=2));temporary.replace(marker)
    print('Migration completion marker saved after all verification steps')
else:print('Existing completion marker retained')
