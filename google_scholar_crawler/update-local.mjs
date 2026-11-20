// Refresh only the citation-data branch, using the current device's network.
import { spawnSync } from 'node:child_process';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const [python, dataDirectory] = process.argv.slice(2);
if (!python || !dataDirectory || !path.isAbsolute(python) || !path.isAbsolute(dataDirectory)) {
  throw new Error('Pass absolute paths: update-local.mjs <python executable> <citation-data checkout>');
}
const scripts = path.dirname(fileURLToPath(import.meta.url));
const env = { ...process.env, GIT_TERMINAL_PROMPT: '0', GCM_INTERACTIVE: 'Never', PYTHONIOENCODING: 'utf-8' };
function run(command, args, cwd) {
  const result = spawnSync(command, args, { cwd, env, encoding: 'utf8', windowsHide: true });
  if (result.status !== 0) throw new Error(`${command} failed: ${result.stderr || result.stdout || result.error}`);
  return result.stdout.trim();
}
const branch = run('git', ['branch', '--show-current'], dataDirectory);
if (branch !== 'google-scholar-stats') throw new Error('Citation checkout is on the wrong branch');
if (run('git', ['status', '--porcelain'], dataDirectory)) throw new Error('Citation checkout has uncommitted changes');
run('git', ['pull', '--ff-only', 'origin', 'google-scholar-stats'], dataDirectory);
const temporary = await mkdtemp(path.join(tmpdir(), 'homepage-scholar-'));
const html = path.join(temporary, 'profile.html');
run(process.execPath, [path.join(scripts, 'fetch-profile.mjs'), html]);
console.log(run(python, [path.join(scripts, 'refresh.py'), '--html', html, '--output', dataDirectory]));
run('git', ['add', 'metrics.json', 'badges'], dataDirectory);
const changed = run('git', ['diff', '--cached', '--name-only'], dataDirectory);
if (changed) {
  run('git', ['commit', '-m', 'Refresh Google Scholar citation badges'], dataDirectory);
  run('git', ['push', 'origin', 'HEAD:google-scholar-stats'], dataDirectory);
  console.log('Published refreshed citation badges.');
}
