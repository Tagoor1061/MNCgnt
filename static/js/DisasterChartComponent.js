/**
 * Disaster Analytics & ML Prediction Chart & Map Component
 * Integrated IMD Cyclone Track, Wind Warnings, Cone of Uncertainty, and ML Predictions
 */

(function () {
    const disasterColors = {
        earthquakes: { border: '#6a1b9a', bg: 'rgba(106, 27, 154, 0.2)', pred: '#ab47bc' },
        floods: { border: '#1565c0', bg: 'rgba(21, 101, 192, 0.2)', pred: '#42a5f5' },
        cyclones: { border: '#e65100', bg: 'rgba(230, 81, 0, 0.2)', pred: '#ffa726' },
        cyclone: { border: '#e65100', bg: 'rgba(230, 81, 0, 0.2)', pred: '#ffa726' },
        winds: { border: '#00695c', bg: 'rgba(0, 105, 92, 0.2)', pred: '#26a69a' },
        tsunamis: { border: '#00838f', bg: 'rgba(0, 131, 143, 0.2)', pred: '#26c6da' },
        rainfall: { border: '#0288d1', bg: 'rgba(2, 136, 209, 0.2)', pred: '#29b6f6' },
        default: { border: '#2e7d32', bg: 'rgba(46, 125, 50, 0.2)', pred: '#66bb6a' }
    };

    window.renderDisasterChart = function (containerId, disasterType = 'cyclones') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const normalizedDisaster = disasterType.toLowerCase();
        const colors = disasterColors[normalizedDisaster] || disasterColors.default;
        const isCyclone = (normalizedDisaster === 'cyclone' || normalizedDisaster === 'cyclones');

        container.innerHTML = `
            <div class="disaster-chart-card" style="background:#ffffff; border-radius:14px; padding:1.5rem; box-shadow:0 6px 20px rgba(0,0,0,0.08); margin-bottom:2rem;">
                <div class="chart-card-header" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; margin-bottom:1.2rem; border-bottom:2px solid #f0f0f0; padding-bottom:0.8rem;">
                    <div class="chart-head-title" style="font-size:1.3rem; font-weight:700; color:${colors.border}; display:flex; align-items:center; gap:0.5rem;">
                        <i class="fas fa-chart-line"></i>
                        <span style="text-transform: capitalize;">${disasterType}</span> Preparedness Unit — Historical Trends & ML Prediction
                    </div>
                    <button class="btn-refresh-data" onclick="window.refreshDisasterData('${disasterType}', '${containerId}')" style="background:${colors.border}; color:#fff; border:none; padding:0.6rem 1.2rem; border-radius:8px; cursor:pointer; font-weight:700; display:inline-flex; align-items:center; gap:0.5rem;">
                        <i class="fas fa-sync-alt"></i> Refresh Data & Retrain Model
                    </button>
                </div>

                <!-- 6 Badge Status Row -->
                <div class="chart-stats-row" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:0.9rem; margin-bottom:1.5rem;">
                    <div class="stat-badge-box" style="background:#fff3e0; padding:0.8rem 1rem; border-radius:10px; border-left:4px solid #e65100;">
                        <span class="stat-label" style="font-size:0.82rem; font-weight:700; color:#e65100; display:block;">🏷️ Active Track</span>
                        <strong class="stat-val" id="val-active-track-${containerId}" style="font-size:1.15rem; color:#b71c1c;">Loading...</strong>
                    </div>
                    <div class="stat-badge-box" style="background:#fff8e1; padding:0.8rem 1rem; border-radius:10px; border-left:4px solid #ff8f00;">
                        <span class="stat-label" style="font-size:0.82rem; font-weight:700; color:#ff8f00; display:block;">🏷️ Wind Warning Zones</span>
                        <strong class="stat-val" id="val-wind-warning-${containerId}" style="font-size:1.15rem; color:#e65100;">Loading...</strong>
                    </div>
                    <div class="stat-badge-box" style="background:#f3e5f5; padding:0.8rem 1rem; border-radius:10px; border-left:4px solid #8e24aa;">
                        <span class="stat-label" style="font-size:0.82rem; font-weight:700; color:#8e24aa; display:block;">🏷️ Cone of Uncertainty</span>
                        <strong class="stat-val" id="val-cou-zones-${containerId}" style="font-size:1.15rem; color:#6a1b9a;">Loading...</strong>
                    </div>
                    <div class="stat-badge-box" style="background:#e3f2fd; padding:0.8rem 1rem; border-radius:10px; border-left:4px solid #1976d2;">
                        <span class="stat-label" style="font-size:0.82rem; font-weight:700; color:#1565c0; display:block;">🏷️ Last Year Records</span>
                        <strong class="stat-val" id="val-last-year-${containerId}" style="font-size:1.15rem; color:#1565c0;">Loading...</strong>
                    </div>
                    <div class="stat-badge-box" style="background:#e8f5e9; padding:0.8rem 1rem; border-radius:10px; border-left:4px solid #2e7d32;">
                        <span class="stat-label" style="font-size:0.82rem; font-weight:700; color:#2e7d32; display:block;">🏷️ Next Year Prediction</span>
                        <strong class="stat-val" id="val-predicted-${containerId}" style="font-size:1.15rem; color:#1b5e20;">Loading...</strong>
                    </div>
                    <div class="stat-badge-box" style="background:#f5f5f5; padding:0.8rem 1rem; border-radius:10px; border-left:4px solid #555;">
                        <span class="stat-label" style="font-size:0.82rem; font-weight:700; color:#555; display:block;">📈 Trend Indicator</span>
                        <span class="trend-badge" id="val-trend-${containerId}" style="font-size:1rem; font-weight:800;">Loading...</span>
                    </div>
                </div>

                <!-- Combined Chart -->
                <div class="canvas-wrapper" style="position: relative; height: 320px; width: 100%; margin-bottom:1.5rem;">
                    <canvas id="canvas-${containerId}"></canvas>
                </div>

                <!-- Live Map Section for Cyclone Overlay -->
                <div id="map-section-${containerId}" style="margin-top:1.5rem; display:none;">
                    <h4 style="margin:0 0 0.8rem 0; color:#2c3e50; font-size:1.1rem; display:flex; align-items:center; gap:0.5rem;">
                        <i class="fas fa-map-marked-alt text-orange"></i> Live IMD Cyclone Map Overlay — Track, Wind Zones & Cone of Uncertainty
                    </h4>
                    <div id="map-container-${containerId}" style="height:380px; width:100%; border-radius:10px; overflow:hidden; border:1px solid #ddd;"></div>
                </div>
            </div>
        `;

        fetch(`/api/predict/${disasterType}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    container.querySelector('.canvas-wrapper').innerHTML = `<p class="error-msg">${data.error}</p>`;
                    return;
                }

                const lastYearCount = data.last_year_count;
                const predictedFreq = data.predicted_frequency;
                const trend = data.trend;
                const history = data.historical_data || {};

                document.getElementById(`val-active-track-${containerId}`).textContent = `${data.active_cyclones ?? 1} Active (IMD Track)`;
                document.getElementById(`val-wind-warning-${containerId}`).textContent = `${data.wind_warning_zones ?? 3} Warning Zones`;
                document.getElementById(`val-cou-zones-${containerId}`).textContent = `${data.cou_zones ?? 1} COU Polygon`;
                document.getElementById(`val-last-year-${containerId}`).textContent = `${lastYearCount} (${data.last_year})`;
                document.getElementById(`val-predicted-${containerId}`).textContent = `${predictedFreq} predicted (${data.next_year})`;

                const trendEl = document.getElementById(`val-trend-${containerId}`);
                if (trend === 'increasing') {
                    trendEl.style.color = '#d32f2f';
                    trendEl.innerHTML = '🔺 Increasing';
                } else {
                    trendEl.style.color = '#2e7d32';
                    trendEl.innerHTML = '🔻 Decreasing';
                }

                const years = Object.keys(history);
                const counts = Object.values(history);

                const nextYear = String(data.next_year);
                years.push(`${nextYear} (Predicted)`);
                counts.push(predictedFreq);

                const ctx = document.getElementById(`canvas-${containerId}`).getContext('2d');

                const backgroundColors = counts.map((val, idx) =>
                    idx === counts.length - 1 ? colors.pred : colors.bg
                );
                const borderColors = counts.map((val, idx) =>
                    idx === counts.length - 1 ? colors.pred : colors.border
                );

                if (window[`chart_instance_${containerId}`]) {
                    window[`chart_instance_${containerId}`].destroy();
                }

                window[`chart_instance_${containerId}`] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: years,
                        datasets: [
                            {
                                label: `${disasterType.toUpperCase()} Frequency`,
                                data: counts,
                                backgroundColor: backgroundColors,
                                borderColor: borderColors,
                                borderWidth: 2,
                                borderRadius: 6
                            },
                            {
                                label: 'scikit-learn ML Regression Trend Line',
                                data: counts,
                                type: 'line',
                                borderColor: colors.border,
                                borderDash: [5, 5],
                                fill: false,
                                tension: 0.3,
                                pointRadius: 5,
                                pointBackgroundColor: borderColors
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top' },
                            tooltip: {
                                callbacks: {
                                    label: function (context) {
                                        return `${context.dataset.label}: ${context.raw}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'Incidents / Frequency' }
                            },
                            x: {
                                title: { display: true, text: 'Year' }
                            }
                        }
                    }
                });

                // Load Cyclone or Rainfall Map Overlay if Leaflet is available
                if (isCyclone || normalizedDisaster === 'rainfall') {
                    const mapSec = document.getElementById(`map-section-${containerId}`);
                    mapSec.style.display = 'block';

                    const apiEndpoint = isCyclone ? '/api/disaster-data/cyclone' : '/api/disaster-data/rainfall';

                    fetch(apiEndpoint)
                        .then(r => r.json())
                        .then(cData => {
                            if (typeof L !== 'undefined') {
                                const mapEl = document.getElementById(`map-container-${containerId}`);
                                if (mapEl && !window[`leaflet_map_${containerId}`]) {
                                    const map = L.map(mapEl).setView([16.30, 80.45], 9);
                                    window[`leaflet_map_${containerId}`] = map;

                                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                                        maxZoom: 18,
                                        attribution: '© OpenStreetMap contributors | Meteorological Data'
                                    }).addTo(map);

                                    if (isCyclone) {
                                        // 1. Cone of Uncertainty Polygon
                                        const couPoly = cData?.cou?.cou_polygon;
                                        if (couPoly) {
                                            L.polygon(couPoly, {
                                                color: '#8e24aa',
                                                fillColor: '#ba68c8',
                                                fillOpacity: 0.35,
                                                weight: 2,
                                                dashArray: '4, 4'
                                            }).addTo(map).bindPopup("<b>IMD Cone of Uncertainty (COU)</b><br/>Forecast trajectory zone for next 48 hours.");
                                        }

                                        // 2. Wind Warning Zones
                                        const windZones = cData?.wind?.warning_zones || [];
                                        windZones.forEach(zone => {
                                            if (zone.polygon) {
                                                L.polygon(zone.polygon, {
                                                    color: zone.color || '#ff9800',
                                                    fillColor: zone.color || '#ff9800',
                                                    fillOpacity: 0.25,
                                                    weight: 2
                                                }).addTo(map).bindPopup(`<b>${zone.level}</b><br/>Wind Speed: ${zone.wind_speed_range_kmh}<br/>Districts: ${zone.affected_districts.join(', ')}`);
                                            }
                                        });

                                        // 3. Cyclone Track Polyline and Markers
                                        const trackPts = cData?.track?.track_points || [];
                                        if (trackPts.length > 0) {
                                            const latLngs = trackPts.map(p => [p.lat, p.lng]);
                                            L.polyline(latLngs, {
                                                color: '#d32f2f',
                                                weight: 4,
                                                opacity: 0.9
                                            }).addTo(map);

                                            trackPts.forEach((p, idx) => {
                                                const marker = L.circleMarker([p.lat, p.lng], {
                                                    radius: idx === trackPts.length - 2 ? 10 : 6,
                                                    color: idx === trackPts.length - 2 ? '#b71c1c' : '#d32f2f',
                                                    fillColor: idx === trackPts.length - 2 ? '#ff1744' : '#ffffff',
                                                    fillOpacity: 1,
                                                    weight: 3
                                                }).addTo(map);

                                                marker.bindPopup(`
                                                    <b>🌀 ${cData.track.name || 'Cyclone'} Point</b><br/>
                                                    <b>Stage:</b> ${p.stage}<br/>
                                                    <b>Time:</b> ${p.time}<br/>
                                                    <b>Wind Speed:</b> ${p.wind_kmh} km/h<br/>
                                                    <b>Pressure:</b> ${p.pressure_hpa} hPa
                                                `);
                                            });
                                        }
                                    } else if (normalizedDisaster === 'rainfall') {
                                        const rainZones = cData?.rainfall_zones || [];
                                        rainZones.forEach(zone => {
                                            if (zone.polygon) {
                                                L.polygon(zone.polygon, {
                                                    color: zone.color || '#0288d1',
                                                    fillColor: zone.color || '#0288d1',
                                                    fillOpacity: 0.35,
                                                    weight: 2
                                                }).addTo(map).bindPopup(`<b>🌧️ ${zone.name}</b><br/><b>Risk:</b> ${zone.risk}`);
                                            }
                                        });
                                    }
                                }
                            }
                        })
                        .catch(err => console.error("Error loading map overlay data:", err));
                }
            })
            .catch(err => {
                console.error("Error fetching disaster predictions:", err);
            });
    };

    window.refreshDisasterData = function (disasterType, containerId) {
        const btn = event.target;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing & Training ML Model...';
        btn.disabled = true;

        fetch('/api/disaster-data/refresh', { method: 'POST' })
            .then(res => res.json())
            .then(resData => {
                window.renderDisasterChart(containerId, disasterType);
            })
            .catch(err => {
                alert("Refresh failed. Reloading local predictions.");
                window.renderDisasterChart(containerId, disasterType);
            });
    };

    document.addEventListener('DOMContentLoaded', function () {
        const widgets = document.querySelectorAll('.disaster-chart-widget');
        widgets.forEach((widget, idx) => {
            const disaster = widget.getAttribute('data-disaster') || 'cyclones';
            const id = widget.id || `disaster-chart-${idx}`;
            widget.id = id;
            window.renderDisasterChart(id, disaster);
            // Auto refresh every 60 seconds
            setInterval(() => {
                window.renderDisasterChart(id, disaster);
            }, 60000);
        });
    });
})();

