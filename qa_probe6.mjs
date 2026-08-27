export default async function run(page, ui) {
  const result = await page.evaluate("() => 'L=' + typeof window.L + ' readyState=' + document.readyState");
  const snap = await ui.snapshot();
  return { value: result, snapshot: String(snap).slice(0, 200) };
}
