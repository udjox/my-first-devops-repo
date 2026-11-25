from common import *
import hashlib, uuid, struct, zlib

version = wait_http()
if (STATE / 'seed-manifest.json').exists():
    print('Seed already exists; original data retained');raise SystemExit(0)
try:
    user, token = login()
except urllib.error.HTTPError:
    api('POST','/users',{'email':'practiceadmin@example.test','username':'practiceadmin','password':settings()['MM_ADMIN_PASSWORD']})
    user, token = login()
team, _ = api('POST','/teams',{'name':'devops-practice','display_name':'Практика DevOps','type':'O'},token)
channel, _ = api('POST','/channels',{'team_id':team['id'],'name':'migration-check','display_name':'Проверка миграции','type':'P'},token)
messages = [
 'Практика 4: сообщения созданы в Mattermost 9.5 на MySQL.',
 'Перед переносом создаём резервную копию базы и пользовательских файлов.',
 'Эта запись должна сохраниться после перехода на PostgreSQL.',
 'Приватный канал и его участники должны сохраниться.',
 'Повторный запуск workflow пропускает уже выполненную миграцию.',
]
posts=[]
for text in messages:
    post,_=api('POST','/posts',{'channel_id':channel['id'],'message':text},token)
    posts.append({'id':post['id'],'message':text})
# Прикладываем реальный файл и аватар для проверки общего Docker Volume.
attachment='Контрольный файл практики 4. Вложения сохраняются после миграции.\n'.encode()
def multipart(field, name, payload, mime, extra=None):
    boundary='mmpractice'+uuid.uuid4().hex;body=b''
    for key,value in (extra or {}).items():
        body+=f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode()
    body+=f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+payload+b'\r\n'+f'--{boundary}--\r\n'.encode()
    return body,'multipart/form-data; boundary='+boundary
body,ctype=multipart('files','migration-check.txt',attachment,'text/plain',{'channel_id':channel['id']})
info,_=api('POST','/files',token=token,raw=body,content_type=ctype);file_id=info['file_infos'][0]['id']
post,_=api('POST','/posts',{'channel_id':channel['id'],'message':'Контрольное вложение для проверки общего тома.','file_ids':[file_id]},token)
posts.append({'id':post['id'],'message':post['message']})
def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
image=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',64,64,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+bytes([30,100,180])*64)*64))+chunk(b'IEND',b'')
body,ctype=multipart('image','avatar.png',image,'image/png')
api('POST','/users/me/image',token=token,raw=body,content_type=ctype)
avatar,_=api('GET','/users/'+user['id']+'/image',token=token)
manifest={'source_version':'9.5.0','user_id':user['id'],'username':'practiceadmin','team_id':team['id'],'channel_id':channel['id'],'channel_name':'migration-check','posts':posts,'file_id':file_id,'file_sha256':hashlib.sha256(attachment).hexdigest(),'avatar_sha256':hashlib.sha256(avatar).hexdigest()}
(STATE/'seed-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(ARTIFACTS/'seed-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Created administrator, team, private channel, 5 messages, attachment and avatar')
