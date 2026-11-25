import fs from 'node:fs';
const values = {
  DB_USER: process.env.DB_USER,
  DB_PASSWORD: process.env.DB_PASSWORD,
  DB_NAME: process.env.DB_NAME,
  APP_PORT: process.env.APP_PORT || '8080',
};
for (const [key, value] of Object.entries(values)) {
  if (!value || /[\r\n\0]/.test(value)) throw new Error(`Missing or invalid ${key}`);
}
if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(values.DB_USER) || !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(values.DB_NAME)) throw new Error('Use simple identifiers for DB_USER and DB_NAME');
if (!/^\d+$/.test(values.APP_PORT) || +values.APP_PORT < 1024 || +values.APP_PORT > 65535) throw new Error('Invalid APP_PORT');
// В одинарных кавычках Compose сохраняет $, # и обратные слеши буквально.
const quote = value => "'" + value.replaceAll("'", "\\'") + "'";
fs.writeFileSync('.env', Object.entries(values).map(([k,v]) => `${k}=${quote(v)}`).join('\n')+'\n', {mode: 0o600});
fs.chmodSync('.env', 0o600);
console.log('.env created without printing secret values');
