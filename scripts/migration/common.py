import json, os, subprocess, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = Path(os.environ.get('MM_STATE_DIR', str(Path.home() / 'Library/Codex/mattermost-practice/state')))
STATE.mkdir(parents=True, exist_ok=True)
ARTIFACTS = ROOT / 'migration-artifacts'
ARTIFACTS.mkdir(exist_ok=True)
ENVFILE = ROOT / '.env.migration'
BASE = 'http://127.0.0.1:8065'
KEYS = ['DB_MYSQL_ROOT_PASSWORD', 'DB_MYSQL_PASSWORD', 'DB_POSTGRES_PASSWORD', 'MM_ADMIN_PASSWORD']

def settings():
    values = {}
    if ENVFILE.exists():
        values.update(line.split('=', 1) for line in ENVFILE.read_text().splitlines() if '=' in line and not line.startswith('#'))
    values.update({key: os.environ[key] for key in KEYS if os.environ.get(key)})
    return values

def redact(text):
    for value in settings().values():
        if value: text = text.replace(value, '***')
    return text

def run(args, capture=False, input=None, log=None, check=True):
    result = subprocess.run([str(a) for a in args], cwd=ROOT, input=input, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = redact((result.stdout or '') + (result.stderr or ''))
    if log: Path(log).write_text(output)
    if not capture and not log and output: print(output, flush=True)
    if check and result.returncode: raise RuntimeError('Command failed: ' + str(args[0]) + ' (see redacted log)\n' + output[-5000:])
    return result.stdout if capture else result

def compose(which, *args, capture=False, **kw):
    file = 'legacy/docker-compose.yml' if which == 'legacy' else 'docker-compose.prod.yml'
    return run(['docker', 'compose', '--env-file', ENVFILE, '-p', 'mattermost-practice', '-f', file, *args], capture=capture, **kw)

def api(method, path, data=None, token=None, raw=None, content_type=None):
    headers = {}
    if token: headers['Authorization'] = 'Bearer ' + token
    body = raw
    if data is not None:
        body = json.dumps(data).encode();headers['Content-Type'] = 'application/json'
    if content_type: headers['Content-Type'] = content_type
    request = urllib.request.Request(BASE + '/api/v4' + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read()
        return (json.loads(content) if content and response.headers.get('Content-Type','').startswith('application/json') else content), response.headers

def login():
    user, headers = api('POST', '/users/login', {'login_id':'practiceadmin', 'password':settings()['MM_ADMIN_PASSWORD']})
    return user, headers['Token']

def wait_http(timeout=300):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            body, headers = api('GET', '/system/ping')
            if body.get('status') == 'OK': return headers.get('X-Version-Id','')
        except Exception: pass
        time.sleep(3)
    raise RuntimeError('Mattermost did not become ready in time')

def pg_query(sql):
    return compose('prod','exec','-T','db-postgres','psql','-U','mmuser','-d','mattermost','-At','-v','ON_ERROR_STOP=1','-c',sql,capture=True).strip()
