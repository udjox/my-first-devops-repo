import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
fs.mkdirSync('artifacts', {recursive:true});
const secretValues = new Set(Object.entries(process.env).filter(([k,v]) => v && /PASSWORD|SECRET|TOKEN|API_KEY/.test(k)).map(([,v])=>v));
// Значения рабочего .env никогда не копируются в артефакт.
if (fs.existsSync('.env')) {
 const keys=fs.readFileSync('.env','utf8').split('\n').filter(line=>/^[A-Z_]+=/.test(line)).map(line=>line.split('=')[0]);
 fs.writeFileSync('artifacts/.env',keys.map(key=>`${key}=***`).join('\n')+'\n');
}
const sanitize = text => {for(const value of secretValues) text=text.split(value).join('***');return text;};
for (const [file,args] of Object.entries({
 'deployment-logs.txt':['compose','logs','--no-color','--tail=200','app','db'],
 'docker-ps.txt':['compose','ps','--all'],
 'docker-images.txt':['images','actions-practice-app:1.0.0'],
})) {
 const result=spawnSync('docker',args,{encoding:'utf8'});
 fs.writeFileSync(`artifacts/${file}`,sanitize((result.stdout||'')+(result.stderr||'')));
}
let results;
try {results=JSON.parse(fs.readFileSync('artifacts/test-results.json','utf8'));}catch {}
const stats=results?.stats;
const passed=!!stats && stats.expected===2 && stats.unexpected===0 && stats.skipped===0;
fs.writeFileSync('artifacts/test-report.md',`# Deployment test report\n\nDate: ${new Date().toISOString()}\n\nStatus: ${passed?'PASSED':'NOT PASSED — inspect logs'}\n\nTests passed: ${stats?.expected ?? 0}; failed: ${stats?.unexpected ?? 'not available'}.\n\nTests verify /healthz, API against direct SQL, all visible item IDs and names, and refresh.\n\nRunner: ${process.env.RUNNER_NAME || 'local execution'}\nGitHub run: ${process.env.GITHUB_RUN_ID || 'not a GitHub Actions run'}\n\nOnly a redacted .env is included.\n`);
console.log('Collected logs, redacted .env and test report in artifacts/');
