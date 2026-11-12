import {spawn, execFileSync} from 'node:child_process';
import {mkdtempSync, mkdirSync, writeFileSync, existsSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import assert from 'node:assert/strict';
import puppeteer from 'puppeteer-core';
import {AxePuppeteer} from '@axe-core/puppeteer';

const python = process.env.PYTHON_BIN || 'python';
const scratch = mkdtempSync(join(tmpdir(), 'toolx-ui-'));
const env = {...process.env, DEBUG: 'True', DJANGO_SETTINGS_MODULE: 'ui_tests.settings', UI_TEST_DB: join(scratch, 'ui.sqlite3')};
const output = resolve('.hallmark/browser');
mkdirSync(output, {recursive: true});
let server, browser;
const report = {checks: [], screenshots: [], errors: []};
try {
  execFileSync(python, ['manage.py', 'migrate', '--noinput'], {env, stdio: 'pipe'});
  const fixture = JSON.parse(execFileSync(python, ['-m', 'ui_tests.seed'], {env, encoding: 'utf8'}));
  server = spawn(python, ['manage.py', 'runserver', '127.0.0.1:4173', '--noreload'], {env, stdio: 'ignore'});
  let ready = false;
  for (let attempt = 0; attempt < 60; attempt++) {
    try { if ((await fetch('http://127.0.0.1:4173/')).ok) { ready = true; break; } } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  assert(ready, 'Django preview did not start.');
  const executablePath = process.env.CHROME_PATH || ['/usr/bin/google-chrome', '/opt/google/chrome/chrome', '/usr/bin/chromium'].find(existsSync);
  browser = await puppeteer.launch({executablePath, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']});
  const page = await browser.newPage();
  page.on('pageerror', error => report.errors.push(error.message));
  const origin = 'http://127.0.0.1:4173';
  const routes = [['home', '/', null], ['login', '/login/', null], ['signup', '/signup/', null], ['reset', '/password_reset/', null],
    ['dashboard', '/dashboard/', 'writer'], ['letters', '/my_adcopies/', 'writer'], ['drafts', '/paraphrase/', 'writer'],
    ['editor', '/create/', 'writer'], ['draft-editor', '/create_paraphrase/', 'writer'], ['profile', '/profile/', 'writer'],
    ['edit-profile', '/profile/edit', 'writer'], ['letter-preview', `/preview/${fixture.letter}`, 'writer'],
    ['draft-preview', `/paraphrase_preview/${fixture.draft}`, 'writer'], ['dashboard-empty', '/dashboard/', 'empty']];
  for (const [name, path, identity] of routes) {
    await page.deleteCookie({name: 'sessionid', url: origin});
    if (identity) await page.setCookie({name: 'sessionid', value: fixture[identity], url: origin});
    for (const width of [320, 375, 768, 1280, 1440, 1920]) {
      await page.setViewport({width, height: 900});
      const response = await page.goto(origin + path, {waitUntil: 'networkidle2'});
      assert.equal(response.status(), 200, `${name}: HTTP failure`);
      await page.evaluate(() => document.fonts.ready);
      const metrics = await page.evaluate(() => {
        const outside = [...document.querySelectorAll('main *')].filter(el => {
          if (el.closest('.visually-hidden') || el.getClientRects().length === 0) return false;
          const rect = el.getBoundingClientRect();
          return rect.left < -1 || rect.right > innerWidth + 1;
        }).map(el => el.tagName + '.' + el.className).slice(0, 5);
        return {overflow: document.documentElement.scrollWidth > innerWidth + 1, outside};
      });
      assert(!metrics.overflow && !metrics.outside.length, `${name} at ${width}px overflows: ${JSON.stringify(metrics)}`);
      if (width === 375 || width === 1280) {
        const result = await new AxePuppeteer(page).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
        assert.equal(result.violations.length, 0, `${name} at ${width}px: ${JSON.stringify(result.violations.map(v => ({id:v.id, nodes:v.nodes.map(n=>n.target)})))}`);
        const shot = `${name}-${width}.png`;
        await page.screenshot({path: join(output, shot), fullPage: true});
        report.screenshots.push(shot);
      }
      report.checks.push({page:name, width, status:'passed'});
    }
  }
  await page.setViewport({width:375,height:900});
  await page.goto(origin + '/login/');
  await page.type('#id_username', 'unknown');
  await page.type('#id_password', 'incorrect');
  await Promise.all([page.waitForNavigation(), page.click('button[type="submit"]')]);
  assert(await page.$('[role="alert"]'), 'Invalid login must show an error.');
  await page.keyboard.press('Tab');
  await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
  assert.equal(report.errors.length, 0, 'Browser script errors');
  console.log(`${report.checks.length} responsive checks passed; 28 WCAG audits passed; screenshots saved.`);
} finally {
  writeFileSync(join(output, 'report.json'), JSON.stringify(report, null, 2));
  await browser?.close();
  server?.kill();
  rmSync(scratch, {recursive:true, force:true});
}
