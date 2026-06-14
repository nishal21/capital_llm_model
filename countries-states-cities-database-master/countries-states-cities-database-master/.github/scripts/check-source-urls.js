/**
 * Source URL Check (Idea 16)
 * Extracts URLs from PR description and verifies they are accessible (not 404).
 */

const core = require('@actions/core');
const github = require('@actions/github');
const https = require('https');
const http = require('http');

const TIMEOUT_MS = 10000;

/**
 * Check if a URL is accessible via HEAD request.
 * @param {string} url - URL to check
 * @returns {Promise<{url: string, status: number|null, ok: boolean, error: string|null}>}
 */
function checkUrl(url) {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      resolve({ url, status: null, ok: false, error: 'Timeout' });
    }, TIMEOUT_MS);

    try {
      const lib = url.startsWith('https') ? https : http;
      const req = lib.request(url, { method: 'HEAD', timeout: TIMEOUT_MS }, (res) => {
        clearTimeout(timeout);
        const ok = res.statusCode >= 200 && res.statusCode < 400;
        resolve({ url, status: res.statusCode, ok, error: null });
      });

      req.on('error', (err) => {
        clearTimeout(timeout);
        resolve({ url, status: null, ok: false, error: err.message });
      });

      req.on('timeout', () => {
        req.destroy();
        clearTimeout(timeout);
        resolve({ url, status: null, ok: false, error: 'Request timeout' });
      });

      req.end();
    } catch (err) {
      clearTimeout(timeout);
      resolve({ url, status: null, ok: false, error: err.message });
    }
  });
}

async function run() {
  const { pull_request: pr } = github.context.payload;

  if (!pr) {
    core.setFailed('This script must run on a pull_request event.');
    return;
  }

  const body = pr.body || '';

  // Extract URLs from PR description
  const urlPattern = /https?:\/\/[^\s)>"',]+/gi;
  const urls = [...new Set(body.match(urlPattern) || [])];

  // Filter out common non-source URLs
  const excludePatterns = [
    /github\.com\/dr5hn/i,
    /github\.com\/.*\/pull\//i,
    /github\.com\/.*\/issues\//i,
    /countrystatecity\.in/i,
  ];

  const sourceUrls = urls.filter(
    (url) => !excludePatterns.some((p) => p.test(url))
  );

  if (sourceUrls.length === 0) {
    core.info('No source URLs found in PR description.');
    core.setOutput('errors', JSON.stringify([]));
    core.setOutput('valid', '0');
    return;
  }

  core.info(`Checking ${sourceUrls.length} source URL(s)...`);

  const errors = [];
  let validCount = 0;

  // Check each URL (limit to 5 to avoid rate limiting)
  const urlsToCheck = sourceUrls.slice(0, 5);

  for (const url of urlsToCheck) {
    const result = await checkUrl(url);
    if (result.ok) {
      validCount++;
      core.info(`[OK] ${url} (${result.status})`);
    } else {
      const reason = result.error || `HTTP ${result.status}`;
      errors.push(`Source URL unreachable: ${url} (${reason})`);
      core.warning(`[FAIL] ${url} (${reason})`);
    }
  }

  if (sourceUrls.length > 5) {
    core.info(`Only checked first 5 of ${sourceUrls.length} URLs.`);
  }

  core.setOutput('errors', JSON.stringify(errors));
  core.setOutput('valid', validCount.toString());
}

run().catch((err) => core.setFailed(err.message));
