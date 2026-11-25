from common import *
import hashlib
version=wait_http(120)
assert version.startswith('12.0.1.'), 'Unexpected server version: '+version
manifest=json.loads((STATE/'seed-manifest.json').read_text())
source=json.loads((STATE/'source-counts.json').read_text())
user,token=login()
assert user['id']==manifest['user_id'],'User identity changed'
channel,_=api('GET','/channels/'+manifest['channel_id'],token=token)
assert channel['type']=='P','Private channel type was not preserved'
for expected in manifest['posts']:
    post,_=api('GET','/posts/'+expected['id'],token=token)
    assert post['message']==expected['message'],'Message was changed'
file,_=api('GET','/files/'+manifest['file_id'],token=token)
assert hashlib.sha256(file).hexdigest()==manifest['file_sha256'],'Attachment content changed'
avatar,_=api('GET','/users/'+manifest['user_id']+'/image',token=token)
assert hashlib.sha256(avatar).hexdigest()==manifest['avatar_sha256'],'Avatar changed'
counts={table:int(pg_query('SELECT COUNT(*) FROM '+table+';')) for table in source['tables']}
for table, count in source['tables'].items():
    assert counts[table]>=count,'Missing records in '+table
running=run(['docker','ps','--format','{{.Names}}'],capture=True).splitlines()
assert 'mattermost' in running and 'mattermost-postgres' in running
assert 'mattermost-mysql' not in run(['docker','ps','-a','--format','{{.Names}}'],capture=True).splitlines(),'Legacy MySQL container still exists'
image=run(['docker','inspect','mattermost','--format','{{.Config.Image}}'],capture=True).strip()
assert image.endswith(':12.0.1'),image
checks={'version':'12.0.1','private_channel_preserved':True,'messages_preserved':len(manifest['posts']),'attachment_sha256_matches':True,'avatar_sha256_matches':True,'source_counts':source['tables'],'target_counts':counts,'mysql_container_removed':True,'passed':True}
(ARTIFACTS/'data-verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
(ARTIFACTS/'seed-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Verified original user, private channel, messages, attachment, avatar and removal of MySQL container')
