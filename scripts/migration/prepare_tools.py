from common import *
import hashlib, tarfile, urllib.request
binary = ROOT / 'scripts/migration/migration-assist'
if not binary.exists():
    url='https://github.com/mattermost/migration-assist/releases/download/v0.8/migration-assist-Linux-x86_64.tar.gz'
    archive=STATE/'migration-assist-v0.8.tar.gz'
    urllib.request.urlretrieve(url,archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != 'd17e41e38762e79c17324da0dd10dcb9fd0755d97fecd5315bfabbb295b7211b': raise RuntimeError('migration-assist checksum mismatch')
    with tarfile.open(archive) as tf: binary.write_bytes(tf.extractfile('migration-assist').read())
    binary.chmod(0o755)
run(['docker','build','--platform','linux/amd64','-t','mattermost-practice-tools:0.8','-f','scripts/migration/Dockerfile.tools','scripts/migration'],log=ARTIFACTS/'tools-build.log')
print('Official pgloader image and checksum-verified migration-assist v0.8 are ready')
