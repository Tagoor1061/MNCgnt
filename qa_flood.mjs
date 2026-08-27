export default async function run(page, ui) {
  const csp = await page.evaluate(`() => {
    const m = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    return m ? m.content : 'none';
  }`);
  const sw = await page.evaluate(`() =>
    navigator.serviceWorker && navigator.serviceWorker.controller ? 'active' : 'none'`);
  const probe = await page.evaluate(`async () => {
    return new Promise(resolve => {
      const s = document.createElement('script');
      s.src = '/static/lib/leaflet.js?v=' + Date.now();
      s.onload = () => resolve('loaded, L=' + typeof window.L);
      s.onerror = () => resolve('script onerror fired');
      document.head.appendChild(s);
      setTimeout(() => resolve('timeout, L=' + typeof window.L), 8000);
    });
  }`);
  const unitProbe = await page.evaluate(`async () => {
    return new Promise(resolve => {
      const s = document.createElement('script');
      s.src = '/static/js/FloodPreparednessUnit.js?v=' + Date.now();
      s.onload = () => resolve('loaded');
      s.onerror = () => resolve('script onerror fired');
      document.head.appendChild(s);
      setTimeout(() => resolve('timeout'), 8000);
    });
  }`);
  return { csp: csp, sw: sw, leafletProbe: probe, unitProbe: unitProbe };
}
