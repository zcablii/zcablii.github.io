// Fetch the public profile with Node's browser-compatible HTTP client.
// Regional Google Scholar hosts expose the same public profile.
import { writeFile } from 'node:fs/promises';

const destination = process.argv[2];
if (!destination) throw new Error('Pass an output HTML path');
const hosts = ['scholar.google.com', 'scholar.google.com.sg', 'scholar.google.com.hk'];
let lastError;
for (const host of hosts) {
  const url = `https://${host}/citations?user=vKnUqmMAAAAJ&hl=en&pagesize=100`;
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      signal: AbortSignal.timeout(45000),
    });
    const html = await response.text();
    if (!response.ok || !html.includes('class="gsc_a_tr"') || !html.includes('id="gsc_rsb_st"')) {
      throw new Error(`${host}: HTTP ${response.status}, no complete public profile`);
    }
    await writeFile(destination, html, 'utf8');
    console.log(`Fetched public Scholar profile from ${host}`);
    process.exit(0);
  } catch (error) {
    lastError = error;
    console.warn(error.message);
  }
}
throw lastError;
