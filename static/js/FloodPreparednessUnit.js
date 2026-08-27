/**
 * Flood Preparedness Unit — Chart.js + Leaflet Runtime Component
 * ==============================================================
 * Renders the full flood preparedness dashboard:
 *   - 5 status badges (basin discharge, reservoir/gauge alerts, district
 *     warnings, next-year prediction, trend)
 *   - Chart.js line chart: historical discharge + ML/ARIMA AI trajectory
 *   - Leaflet map: floodplain polygons, basin QPF overlay, gauge/reservoir
 *     markers, flash-flood zones
 *   - Manual Refresh button + auto-refresh every 60 seconds
 *
 * Loaded by templates/disasters/floods.html via the
 * #flood-preparedness-widget placeholder div.
 */

(function () {
    const WIDGET_ID = 'flood-preparedness-widget';
    const REFRESH_MS = 60000;

    function riskColor(risk) {
        const r = String(risk || '').toUpperCase();
        if (r === 'EXTREME') return '#d32f2f';
        if (r === 'HIGH') return '#ff9800';
        if (r === 'MODERATE') return '#fbc02d';
        return '#2e7d32';
    }

    window.renderFloodPreparedness = function () {
        const container = document.getElementById(WIDGET_ID);
        if (!container) return;

        container.innerHTML = `
            <div style="background:#ffffff; border-radius:14px; padding:1.5rem; box-shadow:0 6px 20px rgba(0,0,0,0.08); margin-bottom:2rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; margin-bottom:1.2rem; border-bottom:2px solid #e3f2fd; padding-bottom:0.8rem;">
                    <div>
                        <div style="font-size:1.3rem; font-weight:700; color:#1565c0; display:flex; align-items:center; gap:0.5rem;">
                            🌊 Flood Preparedness Unit — IMD + Open-Meteo + Google AI Prediction
                        </div>
                        <small style="color:#666;">IMD District/State Rainfall • Basin QPF • Open-Meteo River Discharge • Google Gauge Status • Classifier + ARIMA AI</small>
                    </div>
                    <button id="flood-refresh-btn" style="background:#1565c0; color:#fff; border:none; padding:0.6rem 1.2rem; border-radius:8px; cursor:pointer; font-weight:700; display:inline-flex; align-items:center; gap:0.5rem;">
                        <i class="fas fa-sync-alt"></i> Manual Refresh & Retrain
                    </button>
                </div>
                <div id="flood-badges" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(165px, 1fr)); gap:0.9rem; margin-bottom:1.5rem;">
                    <div class="flood-badge">Loading…</div>
                </div>
                <div style="position:relative; height:340px; width:100%; margin-bottom:1.5rem;">
                    <canvas id="flood-chart-canvas"></canvas>
                </div>
                <h4 style="margin:0 0 0.8rem 0; color:#2c3e50; font-size:1.1rem; display:flex; align-items:center; gap:0.5rem;">
                    <i class="fas fa-map-marked-alt" style="color:#1565c0;"></i>
                    Live Flood Map — Floodplain Polygons, Basin QPF Overlay & Gauge Markers
                </h4>
                <div id="flood-map" style="height:400px; width:100%; border-radius:10px; overflow:hidden; border:1px solid #ddd;"></div>
                <div id="flood-explain-box" style="margin-top:1.2rem;"></div>
            </div>
            <div style="background:#e8eaf6; border-radius:14px; padding:1.5rem; box-shadow:0 6px 20px rgba(0,0,0,0.08); margin-bottom:2rem;">
                <h4 style="margin:0 0 0.8rem; color:#283593; display:flex; align-items:center; gap:0.5rem;">
                    <i class="fas fa-house-damage" style="color:#1565c0;"></i> Flood Preparedness Guide
                </h4>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:1rem;">
                    <div style="background:#fff; border-radius:10px; padding:1rem;">
                        <strong style="color:#1565c0;">🚸 Evacuation Routes</strong>
                        <ul style="margin:0.5rem 0 0; padding-left:1.2rem; font-size:0.88rem; color:#444;">
                            <li>Move to designated shelters on NH-16 and elevated mandal roads — never through underpasses.</li>
                            <li>Follow municipal announcements; keep away from bunds of the Krishna and Budameru channels at night.</li>
                            <li>Switch off mains power before leaving; carry documents in waterproof bags.</li>
                        </ul>
                    </div>
                    <div style="background:#fff; border-radius:10px; padding:1rem;">
                        <strong style="color:#1565c0;">🏫 Flood Shelters</strong>
                        <ul style="margin:0.5rem 0 0; padding-left:1.2rem; font-size:0.88rem; color:#444;">
                            <li>Guntur Municipal Corporation cyclone/flood shelters & school buildings on high ground.</li>
                            <li>Carry drinking water, dry food, medicines, torch and power bank for 72 hours.</li>
                        </ul>
                    </div>
                    <div style="background:#fff; border-radius:10px; padding:1rem;">
                        <strong style="color:#1565c0;">🏠 Sandbagging & Home Protection</strong>
                        <ul style="margin:0.5rem 0 0; padding-left:1.2rem; font-size:0.88rem; color:#444;">
                            <li>Stack sandbags at doorways and low vents; seal drains with covers to stop backflow.</li>
                            <li>Shift appliances, grain stock and LPG cylinders above expected water level.</li>
                            <li>Do not walk or drive through flowing water — 30 cm can sweep a car away.</li>
                        </ul>
                    </div>
                    <div style="background:#fff; border-radius:10px; padding:1rem;">
                        <strong style="color:#d32f2f;">☎️ Emergency Helplines</strong>
                        <ul style="margin:0.5rem 0 0; padding-left:1.2rem; font-size:0.88rem; color:#444;">
                            <li><b>NDMA:</b> 1078 &nbsp;•&nbsp; <b>SDMA (AP):</b> 1070</li>
                            <li><b>Police:</b> 100 &nbsp;•&nbsp; <b>Fire & Rescue:</b> 101</li>
                            <li><b>Ambulance:</b> 108 &nbsp;•&nbsp; <b>GMC Control Room:</b> 1800-103-4242</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;

        const refreshBtn = document.getElementById('flood-refresh-btn');
        refreshBtn.addEventListener('click', async function () {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing & Retraining…';
            refreshBtn.disabled = true;
            try {
                await fetch('/api/disaster-data/flood/refresh', { method: 'POST' });
            } catch (e) { /* keep rendering cached data */ }
            window.renderFloodPreparedness();
        });

        Promise.all([
            fetch('/api/predict/flood').then(r => r.json()),
            fetch('/api/disaster-data/flood').then(r => r.json())
        ]).then(([pred, live]) => {
            if (window.__floodRenderBadges) window.__floodRenderBadges(pred, live);
            if (window.__floodRenderChart) window.__floodRenderChart(pred);
            if (window.__floodRenderMap) window.__floodRenderMap(live);
            if (window.__floodRenderExplain) window.__floodRenderExplain(pred);
        }).catch(err => {
            console.error('Flood preparedness load failed:', err);
            container.querySelector('#flood-badges').innerHTML =
                '<div class="flood-badge" style="color:#d32f2f;">⚠️ Failed to load flood data. Will retry in 60s.</div>';
        });
    };
})();

/* ------------------------------------------------------------------ *
 * Sub-renderers (attached inside the same IIFE scope)
 * ------------------------------------------------------------------ */
(function () {
    const WARNING_COLORS = {
        red: '#d32f2f', orange: '#ff9800', yellow: '#fbc02d', green: '#2e7d32'
    };

    window.__floodRenderBadges = function (pred, live) {
        const box = document.getElementById('flood-badges');
        if (!box) return;

        const s = live?.summary || {};
        const districts = (live?.imd_qpf?.district_rainfall?.districts) || [];
        const heavyCount = s.heavy_rainfall_districts ??
            districts.filter(d => (d.rainfall_mm || 0) >= 64.5).length;
        const meanQ = s.mean_discharge_m3s ?? '—';
        const curRisk = s.current_risk || 'LOW';

        const badge = (bg, border, label, value, valueColor) => `
            <div style="background:${bg}; padding:0.85rem 1rem; border-radius:10px; border-left:4px solid ${border};">
                <span style="font-size:0.8rem; font-weight:700; color:${border}; display:block;">${label}</span>
                <strong style="font-size:1.05rem; color:${valueColor || border};">${value}</strong>
            </div>`;

        const trendUp = pred?.trend === 'increasing';
        box.innerHTML = [
            badge('#e3f2fd', '#1565c0', '🌊 Basin Discharge',
                `${meanQ} m³/s avg • <span style="color:${riskColor(curRisk)}">${curRisk}</span>`),
            badge('#ede7f6', '#5e35b1', '🌊 Reservoir / Gauge Alerts',
                `${s.reservoir_alerts ?? 0} Alerts • ${s.gauges_reporting ?? 0} Gauges`),
            badge('#fff3e0', '#ff9800', '🌊 District Warnings',
                `<span style="color:${WARNING_COLORS.red}">🔴 ${heavyCount}</span> heavy-rainfall districts
                 • ${s.high_risk_sub_basins ?? 0} high-risk sub-basins`),
            badge('#e0f2f1', '#00897b', `🌊 Next Year Prediction (${pred?.next_year ?? ''})`,
                `${pred?.predicted_high_events_next_year ?? '—'} high-discharge days • Peak ${pred?.peak_forecast_discharge_m3s ?? '—'} m³/s`, '#004d40'),
            badge('#f5f5f5', trendUp ? WARNING_COLORS.red : WARNING_COLORS.green, '📈 Trend Indicator',
                trendUp ? `🔺 Increasing (${pred?.high_discharge_days_this_year ?? 0} days this yr)` : `🔻 Decreasing (${pred?.high_discharge_days_this_year ?? 0} days this yr)`,
                trendUp ? WARNING_COLORS.red : WARNING_COLORS.green),
        ].join('');
    };
})();

(function () {
    window.__floodRenderChart = function (pred) {
        const canvas = document.getElementById('flood-chart-canvas');
        if (!canvas || typeof Chart === 'undefined') return;

        const hist = pred?.daily_history || [];
        const fc = pred?.forecast_trajectory || [];
        if (!hist.length && !fc.length) {
            canvas.replaceWith(Object.assign(document.createElement('div'), {
                innerHTML: '<div style="padding:2rem; text-align:center; color:#888;">⚠️ No discharge history or forecast data available.</div>'
            }));
            return;
        }

        const histLabels = hist.map(h => h.date);
        const histVals = hist.map(h => h.discharge_m3s);
        const fcLabels = fc.map(f => f.date);
        const bridgeIdx = Math.max(histLabels.length - 1, 0);

        if (window.__floodChart) window.__floodChart.destroy();
        window.__floodChart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: [...histLabels, ...fcLabels],
                datasets: [
                    {
                        label: 'Historical River Discharge (m³/s)',
                        data: [...histVals, ...Array(fcLabels.length).fill(null)],
                        borderColor: '#1565c0',
                        backgroundColor: 'rgba(21,101,192,0.15)',
                        fill: true, tension: 0.35, pointRadius: 2, borderWidth: 2
                    },
                    {
                        label: `AI Blended Forecast (${pred?.model_type || pred?.classifier_kind || 'Classifier'} + ARIMA)`,
                        data: [...Array(bridgeIdx).fill(null), histVals[bridgeIdx],
                        ...fc.map(f => f.blended_discharge_m3s)],
                        borderColor: '#e65100', borderDash: [6, 4],
                        fill: false, tension: 0.35, pointRadius: 3, borderWidth: 2.5
                    },
                    {
                        label: 'ML Trajectory',
                        data: [...Array(bridgeIdx).fill(null), histVals[bridgeIdx],
                        ...fc.map(f => f.ml_discharge_m3s)],
                        borderColor: '#5e35b1', borderDash: [4, 4],
                        fill: false, tension: 0.35, pointRadius: 0, borderWidth: 1.5
                    },
                    {
                        label: 'ARIMA Trajectory',
                        data: [...Array(bridgeIdx).fill(null), histVals[bridgeIdx],
                        ...fc.map(f => f.arima_discharge_m3s)],
                        borderColor: '#8e24aa', borderDash: [2, 3],
                        fill: false, tension: 0.35, pointRadius: 0, borderWidth: 1.5
                    }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.raw} m³/s` } }
                },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Discharge (m³/s)' } },
                    x: { title: { display: true, text: 'Date' }, ticks: { maxTicksLimit: 16 } }
                }
            }
        });
    };
})();

(function () {
    function riskColor(risk) {
        const r = String(risk || '').toUpperCase();
        if (r === 'EXTREME') return '#b71c1c';
        if (r === 'HIGH') return '#e53935';
        if (r === 'MODERATE') return '#fb8c00';
        return '#1e88e5';
    }

    window.__floodRenderMap = function (live) {
        const mapEl = document.getElementById('flood-map');
        if (!mapEl || typeof L === 'undefined') return;

        if (window.__floodLeafletMap) {
            window.__floodLeafletMap.remove();
            window.__floodLeafletMap = null;
        }
        const map = L.map(mapEl).setView([16.10, 80.30], 8);
        window.__floodLeafletMap = map;

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '© OpenStreetMap | GMC Flood Preparedness'
        }).addTo(map);

        // ---- Layer 1: basin QPF overlay + sub-basin markers -------------------
        const basin = live?.imd_qpf?.basin_qpf || {};
        if (basin.polygon) {
            L.polygon(basin.polygon, {
                color: '#1565c0', fillColor: '#42a5f5',
                fillOpacity: 0.12, weight: 2
            }).addTo(map).bindPopup(
                `<b>🏞️ ${basin.basin_name || 'River Basin'} QPF</b><br/>` +
                `${(basin.sub_basins || []).map(sb => `${sb.name}: <b>${sb.qpf_mm} mm</b> (${sb.risk})`).join('<br/>')}`);
        }
        (basin.sub_basins || []).forEach((sb, i) => {
            const anchor = basin.polygon && basin.polygon.length
                ? basin.polygon[Math.min(i + 1, basin.polygon.length - 2)]
                : [16.2 + i * 0.15, 80.2];
            if (!anchor) return;
            L.marker(anchor).addTo(map).bindPopup(
                `<b>🏞️ ${sb.name}</b><br/>QPF (24h): <b>${sb.qpf_mm} mm</b><br/>Risk: ${sb.risk}`);
        });

        // ---- Layer 2: floodplain polygons from flash-flood zones --------------
        (live?.google_flood?.flash_floods || []).forEach(z => {
            if (!z.polygon) return;
            const c = riskColor(z.severity);
            L.polygon(z.polygon, {
                color: c, fillColor: c,
                fillOpacity: 0.25, weight: 2.5, dashArray: '6, 3'
            }).addTo(map).bindPopup(
                `<b>🌊 Flash Flood Watch — ${z.area || ''}</b><br/>` +
                `Severity: <b>${z.severity || '—'}</b> (${z.probability_percent ?? '—'}% probability)<br/>` +
                `${z.message || ''}<br/><i>Valid: ${z.valid_from || ''} → ${z.valid_to || ''}</i>`);
        });

        // ---- Layer 3: gauge / reservoir markers --------------------------------
        (live?.google_flood?.gauges || []).forEach(g => {
            const lat = g.lat ?? 16.3067;
            const lon = g.lon ?? 80.4365;
            const c = riskColor(g.status === 'NORMAL' ? 'LOW' : g.status);
            L.circleMarker([lat, lon], {
                radius: 9,
                color: c, fillColor: c, fillOpacity: 0.75, weight: 2
            }).addTo(map).bindPopup(
                `<b>💧 ${g.site_name || g.gauge_id}</b><br/>Status: <b>${g.status || '—'}</b><br/>` +
                `Discharge: <b>${g.discharge_m3s ?? '—'} m³/s</b><br/>` +
                `Forecast peak: ${g.forecast_peak_m3s ?? '—'} m³/s (${g.forecast_time || ''})<br/>` +
                `${g.message || ''}`);
        });

        // ---- Layer 4: heavy-rainfall district heat circles ---------------------
        ((live?.imd_qpf?.district_rainfall)?.districts || []).forEach(d => {
            if (d.lat == null || d.lon == null) return;
            const mm = d.rainfall_mm || 0;
            const c = mm >= 115.6 ? '#b71c1c' : mm >= 64.5 ? '#e53935' : mm >= 15.6 ? '#1e88e5' : '#90caf9';
            L.circle([d.lat, d.lon], {
                radius: 12000 + Math.min(mm * 100, 14000),
                color: c, fillColor: c, fillOpacity: 0.3, weight: 1.5
            }).addTo(map).bindPopup(
                `<b>🌧️ ${d.district}</b><br/>Rainfall: <b>${mm} mm</b> (${d.category || '—'})<br/>` +
                `Departure: ${d.departure_percent > 0 ? '+' : ''}${d.departure_percent}%`);
        });

        // Legend control
        const legend = L.control({ position: 'bottomright' });
        legend.onAdd = function () {
            const div = L.DomUtil.create('div');
            div.style.cssText = 'background:#fff;padding:8px 10px;border-radius:8px;font-size:0.75rem;line-height:1.5;box-shadow:0 2px 8px rgba(0,0,0,0.25);';
            div.innerHTML =
                '<b>Flood Risk Levels</b><br/>' +
                '<span style="color:#1e88e5">●</span> LOW (normal)&lt;500 m³/s<br/>' +
                '<span style="color:#fb8c00">●</span> MODERATE (500–750)<br/>' +
                '<span style="color:#e53935">●</span> HIGH (750–1000)<br/>' +
                '<span style="color:#b71c1c">●</span> EXTREME (&gt;1000)';
            return div;
        };
        legend.addTo(map);
    };
})();

(function () {
    window.__floodRenderExplain = function (pred) {
        const box = document.getElementById('flood-explain-box');
        if (!box) return;
        const shap = pred?.explainability?.shap_feature_importance || {};
        const lime = pred?.explainability?.lime_local_explanation || [];
        const entries = Object.entries(shap);
        const maxVal = Math.max(...entries.map(([, v]) => Math.abs(v)), 0.0001);

        const shapRows = entries.length
            ? entries.map(([feat, val]) => `
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.35rem;">
                    <span style="width:110px; font-size:0.8rem; color:#555;">${feat}</span>
                    <div style="flex:1; background:#eceff1; border-radius:4px; height:10px; overflow:hidden;">
                        <div style="width:${(Math.abs(val) / maxVal) * 100}%; height:100%; background:linear-gradient(90deg,#0288d1,#e65100);"></div>
                    </div>
                    <span style="width:56px; text-align:right; font-size:0.75rem; color:#777;">${val}</span>
                </div>`).join('')
            : '<span style="font-size:0.85rem; color:#888;">⚠️ SHAP feature importance not available.</span>';

        let limeRows;
        if (Array.isArray(lime) && lime.length) {
            limeRows = lime.map(item => `
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; padding:0.25rem 0.5rem; background:#f5f5f5; border-radius:4px; margin-bottom:0.3rem;">
                    <span>${item.feature}</span>
                    <strong style="color:${item.weight >= 0 ? '#2e7d32' : '#d32f2f'};">${item.weight >= 0 ? '+' : ''}${item.weight}</strong>
                </div>`).join('');
        } else if (lime && typeof lime === 'object') {
            limeRows = `<pre style="margin:0; font-size:0.78rem; background:#f5f5f5; padding:0.7rem; border-radius:6px; overflow-x:auto; white-space:pre-wrap;">${JSON.stringify(lime, null, 2)}</pre>`;
        } else {
            limeRows = '<span style="font-size:0.85rem; color:#888;">⚠️ LIME local explanation not available.</span>';
        }

        box.innerHTML = `
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:1rem;">
                <div style="background:#fafafa; border:1px solid #eee; border-radius:10px; padding:1rem;">
                    <h4 style="margin:0 0 0.6rem; color:#37474f;">🧠 AI Flood Risk Assessment</h4>
                    <p style="margin:0.2rem 0;">Current Risk:
                        <strong style="color:${pred?.current_risk_color || '#37474f'}; font-size:1.05rem;">${pred?.current_risk ?? '—'}</strong></p>
                    <p style="margin:0.2rem 0;">Peak Forecast:
                        <strong>${pred?.peak_forecast_day ?? '—'}</strong> (${pred?.peak_forecast_discharge_m3s ?? '—'} m³/s)</p>
                    <p style="margin:0.2rem 0;">High-Discharge Days Next Year:
                        <strong>${pred?.predicted_high_events_next_year ?? '—'}</strong></p>
                    <p style="margin:0.2rem 0; font-size:0.82rem; color:#777;">
                        Model: ${pred?.classifier_kind ?? '—'} • ARIMA AIC: ${pred?.arima?.aic ?? 'n/a'} • Trained: ${pred?.trained_at ?? '—'}</p>
                </div>
                <div style="background:#fafafa; border:1px solid #eee; border-radius:10px; padding:1rem;">
                    <h4 style="margin:0 0 0.6rem; color:#37474f;">🔍 SHAP — Feature Influence on Flood Forecast</h4>
                    ${shapRows}
                </div>
                <div style="background:#fafafa; border:1px solid #eee; border-radius:10px; padding:1rem;">
                    <h4 style="margin:0 0 0.6rem; color:#37474f;">🔎 LIME — Latest Prediction Breakdown</h4>
                    ${limeRows}
                </div>
            </div>`;
    };
})();

/* ------------------------------------------------------------------ *
 * Bootstrap + auto-refresh (60s)
 * ------------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', function () {
    if (!document.getElementById('flood-preparedness-widget')) return;

    window.renderFloodPreparedness();          // initial render
    setInterval(window.renderFloodPreparedness, 60000); // auto-refresh every 60s
});
