const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
test('Original private channel and messages survive migration in web interface',async({page})=>{
  const state=process.env.MM_STATE_DIR||path.join(os.homedir(),'Library/Codex/mattermost-practice/state');
  const seed=JSON.parse(fs.readFileSync(path.join(state,'seed-manifest.json'),'utf8'));
  await page.goto('/login');
  const browserButton=page.getByText('View in Browser',{exact:true});
  try { await browserButton.waitFor({state:'visible',timeout:5000}); await browserButton.click(); } catch {}
  await page.locator('#input_loginId').fill(seed.username);
  await page.locator('input[type=password]').fill(process.env.MM_ADMIN_PASSWORD);
  await page.getByRole('button',{name:'Log in',exact:true}).click();
  await expect(page.locator('#input_loginId')).not.toBeVisible();
  await page.goto('/devops-practice/channels/migration-check');
  const dismiss=page.getByText('No thanks, I’ll figure it out myself',{exact:true});
  try { await dismiss.waitFor({state:'visible',timeout:3000}); await dismiss.click(); } catch {}
  for(const post of seed.posts){
    await expect(page.getByText(post.message,{exact:true})).toBeVisible({timeout:60000});
  }
  await expect(page.getByText('migration-check.txt',{exact:true}).first()).toBeVisible();
  fs.mkdirSync('migration-artifacts',{recursive:true});
  await page.screenshot({path:'migration-artifacts/mattermost-after.png',fullPage:true});
  fs.writeFileSync('migration-artifacts/browser-verification.json',JSON.stringify({passed:true,channel:seed.channel_name,visible_messages:seed.posts.map(p=>p.message),attachment_visible:true},null,2));
});
