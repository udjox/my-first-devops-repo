// Запускать после gh auth login и создания репозитория.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const repo=(process.argv[2]||'').replace(/^https:\/\/github.com\//,'').replace(/\/$/,'').replace(/\.git$/,'');
if(!/^[\w.-]+\/[\w.-]+$/.test(repo)) throw new Error('Usage: node scripts/configure-github.mjs OWNER/REPO');
const gh=(args,options={})=>execFileSync('gh',args,{encoding:'utf8',...options});
gh(['auth','status'],{stdio:'inherit'});
const repository=JSON.parse(gh(['repo','view',repo,'--json','nameWithOwner,url']));
const configEnvironment=execFileSync('docker',['compose','config','--environment'],{encoding:'utf8'});
const environment=Object.fromEntries(configEnvironment.split('\n').filter(line=>line.includes('=')).map(line=>{const i=line.indexOf('=');return [line.slice(0,i),line.slice(i+1)];}));
for(const [key,value] of Object.entries({DB_USER:environment.DB_USER,DB_PASSWORD:environment.DB_PASSWORD,DB_NAME:environment.DB_NAME})){
 gh(['secret','set',key,'--repo',repo],{input:value,stdio:['pipe','ignore','inherit']});
 console.log(`Configured repository secret ${key}`);
}
const runnerDir=process.env.PRACTICE_RUNNER_DIR||path.join(os.homedir(),'Library','Application Support','Codex','practice-actions-runner');
if(!fs.existsSync(path.join(runnerDir,'config.sh'))) throw new Error('Install the official macOS ARM64 Actions runner first; see README');
if(fs.existsSync(path.join(runnerDir,'.runner'))){
 const existing=JSON.parse(fs.readFileSync(path.join(runnerDir,'.runner'),'utf8'));
 if(existing.gitHubUrl?.replace(/\/$/,'').toLowerCase()!==repository.url.toLowerCase()) throw new Error('Runner is already registered to another repository');
 console.log('Runner already registered to this repository');
}else{
 const registration=JSON.parse(gh(['api','--method','POST',`repos/${repo}/actions/runners/registration-token`]));
 execFileSync('./config.sh',['--unattended','--url',repository.url,'--token',registration.token,'--name',`${os.hostname().split('.')[0]}-practice`,'--labels','practice-actions','--work','_work'],{cwd:runnerDir,stdio:'inherit'});
}
execFileSync('./svc.sh',['install'],{cwd:runnerDir,stdio:'inherit'});
execFileSync('./svc.sh',['start'],{cwd:runnerDir,stdio:'inherit'});
console.log('Runner service started. Verify Online status in repository Settings > Actions > Runners.');
