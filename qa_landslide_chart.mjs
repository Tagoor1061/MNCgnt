/**
 * Headless verification that __landslideRenderChart renders the
 * citizen-friendly daily timeline without errors.
 */
import { readFileSync } from 'fs';

const calls = { chart: 0, datasets: 0, type: '' };

const fakeCanvas = { id: 'landslide-chart-canvas', getContext: () => ({}) };
const elements = {
    'landslide-chart-wrap': { innerHTML: '', appendChild() {} },
    'landslide-chart-canvas': fakeCanvas,
};

globalThis.window = {};
globalThis.document = {
    getElementById: (id) => elements[id] || null,
    createElement: () => ({ id: '', getContext: () => ({}) }),
    addEventListener: () => {},
};
globalThis.Chart = class {
    constructor(ctx, cfg) {
        calls.chart++;
        calls.datasets = cfg.data.datasets.length;
        calls.type = cfg.type;
    }
    destroy() {}
};

eval(readFileSync('static/js/LandslidePreparednessUnit.js', 'utf8'));

// 3 days of history like the API returns (rainfall in mm/h)
const pred = {
    recent_history: [
        { date: '2026-08-21', rainfall_intensity_mm_h: 1.0, soil_moisture_frac: 0.45, risk: 'LOW' },
        { date: '2026-08-22', rainfall_intensity_mm_h: 4.0, soil_moisture_frac: 0.62, risk: 'HIGH' },
        { date: '2026-08-23', rainfall_intensity_mm_h: 5.5, soil_moisture_frac: 0.68, risk: 'EXTREME' },
    ],
};

window.__landslideRenderChart(pred);

// Expect 4 datasets: rainfall bars + soil line + 2 threshold guide lines
if (calls.chart === 1 && calls.datasets === 4 && calls.type === 'bar') {
    console.log(`CHART_RENDER_OK type=${calls.type} datasets=${calls.datasets}`);
} else {
    console.log(`CHART_RENDER_FAILED chartCalls=${calls.chart} datasets=${calls.datasets} type=${calls.type}`);
    process.exit(1);
}