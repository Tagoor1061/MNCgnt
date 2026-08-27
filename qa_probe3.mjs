export default async function run(page, ui) {
  const result = await page.evaluate("() => 'L=' + typeof window.L + ' readyState=' + document.readyState");
  return 'SIMPLE=' + String(result);
}
