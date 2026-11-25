from common import ENVFILE, KEYS, settings
import re
values = settings()
for key in KEYS:
    if key not in values or not re.fullmatch(r'[A-Za-z0-9!._-]{16,128}', values[key]):
        raise RuntimeError('Missing or unsupported secret: ' + key + '; use at least 16 URL-safe characters')
ENVFILE.write_text(''.join(key + '=' + values[key] + '\n' for key in KEYS))
ENVFILE.chmod(0o600)
print('Migration environment created; secret values are hidden')
