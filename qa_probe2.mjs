export default async function run(page, ui) {
  const result = await page.evaluate(`() => new Promise(resolve => {
    const s = document.createElement('script');
    s.src = '/static/lib/leaflet.js';
    s.onload = () => resolve('LOADED, L=' + typeof window.L);
    s.onerror = () => resolve('ONERROR fired');
    document.body.appendChild(s);
    setTimeout(() => resolve('TIMEOUT, L=' + typeof window.L), 8000);
  })`);
  const snap = await ui.snapshot();
  return 'PROBE=' + String(result) + ' SNAPLEN=' + (typeof snap === 'string' ? snap.length : -1) + ' TYPE=' + typeof result;
}
