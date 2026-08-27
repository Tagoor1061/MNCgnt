export default async function run(page, ui) {
  const result = await page.evaluate("() => 'L=' + typeof window.L + ' readyState=' + document.readyState");
  await ui.snapshot();
  return { value: result };
}
