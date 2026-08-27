import React, { useEffect, useState, useRef } from 'react';
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement,
    LineElement, BarElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement,
    BarElement, Title, Tooltip, Legend, Filler);

const WARNING_COLORS = { Red: '#d32f2f', Orange: '#ff9800', Yellow: '#fbc02d', Green: '#2e7d32' };

const RainfallPredictorChart = () => {
    const [predictData, setPredictData] = useState(null);
    const [rainfallData, setRainfallData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [lastRefreshed, setLastRefreshed] = useState(null);
    const intervalRef = useRef(null);

    const fetchData = async () => {
        try {
            const [predRes, rainRes] = await Promise.all([
                fetch('/api/predict/rainfall'),
                fetch('/api/disaster-data/rainfall'),
            ]);
            setPredictData(await predRes.json());
            setRainfallData(await rainRes.json());
            setLastRefreshed(new Date().toLocaleTimeString());
        } catch (err) {
            console.error('Error fetching rainfall preparedness data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        try {
            await fetch('/api/disaster-data/rainfall/refresh', { method: 'POST' });
            await fetchData();
        } catch (err) {
            console.error('Manual refresh failed:', err);
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
        intervalRef.current = setInterval(fetchData, 60000); // auto-refresh 60s
        return () => clearInterval(intervalRef.current);
    }, []);

    if (loading) {
        return <div className="rainfall-loading">Loading IMD Rainfall Analytics & AI Forecast Models...</div>;
    }
    /* ---------------- chart data: history + AI trajectory ---------------- */
    const monthlyHistory = predictData?.monthly_history || [];
    const forecastTrajectory = predictData?.forecast_trajectory || [];
    const histLabels = monthlyHistory.map(m => m.date);
    const histValues = monthlyHistory.map(m => m.rainfall_mm);
    const fcLabels = forecastTrajectory.map(f => f.date);
    const fcBlended = forecastTrajectory.map(f => f.blended_mm);
    const fcSarima = forecastTrajectory.map(f => f.sarima_mm);
    const bridgeIdx = Math.max(histLabels.length - 1, 0);

    const chartConfig = {
        labels: [...histLabels, ...fcLabels],
        datasets: [
            {
                label: 'Historical Monthly Rainfall (mm)',
                data: [...histValues, ...Array(fcLabels.length).fill(null)],
                borderColor: '#0277bd',
                backgroundColor: 'rgba(2, 119, 189, 0.15)',
                fill: true, tension: 0.35, pointRadius: 2, borderWidth: 2,
            },
            {
                label: `AI Prediction (${predictData?.model_type || 'LSTM'} + SARIMA)`,
                data: [...Array(bridgeIdx).fill(null), histValues[bridgeIdx], ...fcBlended],
                borderColor: '#e65100',
                borderDash: [6, 4],
                fill: false, tension: 0.35, pointRadius: 3, borderWidth: 2.5,
            },
            {
                label: 'SARIMA Seasonal Forecast',
                data: [...Array(bridgeIdx).fill(null), histValues[bridgeIdx], ...fcSarima],
                borderColor: '#8e24aa',
                borderDash: [2, 3],
                fill: false, tension: 0.35, pointRadius: 0, borderWidth: 1.5,
            },
        ],
    };

    /* ---------------- badges ---------------- */
    const summary = rainfallData?.summary || {};
    const warnings = rainfallData?.district_warnings?.warnings || [];
    const redCount = warnings.filter(w => /red/i.test(w.warning_level || '')).length;
    const orangeCount = warnings.filter(w => /orange/i.test(w.warning_level || '')).length;
    const yellowCount = warnings.filter(w => /yellow/i.test(w.warning_level || '')).length;
    const greenCount = warnings.filter(w => /green|no warning/i.test(w.warning_level || '')).length;

    const shapEntries = Object.entries(predictData?.explainability?.shap_feature_importance || {});
    const maxShap = Math.max(...shapEntries.map(([, v]) => v), 0.0001);
    return (
        <div className="rainfall-preparedness-unit" style={{ background: '#ffffff', padding: '1.8rem', borderRadius: '14px', boxShadow: '0 8px 25px rgba(0,0,0,0.08)', marginBottom: '2rem' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', borderBottom: '2px solid #e1f5fe', paddingBottom: '0.8rem' }}>
                <div>
                    <h2 style={{ margin: 0, color: '#0277bd', fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        🌧️ Rainfall Preparedness Unit — IMD Analytics & AI Prediction
                    </h2>
                    <small style={{ color: '#666' }}>
                        Connected to IMD District/State Rainfall, Warnings, Station Nowcast & River Basin QPF APIs
                        {lastRefreshed && <> • Last updated {lastRefreshed}</>}
                    </small>
                </div>
                <button onClick={handleRefresh} disabled={refreshing}
                    style={{ background: '#0277bd', color: '#fff', border: 'none', padding: '0.7rem 1.4rem', borderRadius: '8px', cursor: refreshing ? 'wait' : 'pointer', fontWeight: 700 }}>
                    {refreshing ? '🔄 Refreshing & Retraining...' : '🔄 Manual Refresh & Retrain'}
                </button>
            </div>

            {/* Badges grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '1rem', marginBottom: '1.8rem' }}>
                <div style={{ background: '#e1f5fe', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #0277bd' }}>
                    <small style={{ color: '#0277bd', fontWeight: 700, display: 'block' }}>🏷️ District-wise Rainfall Records</small>
                    <strong style={{ fontSize: '1.4rem', color: '#01579b' }}>{summary.district_records ?? '—'} Districts</strong>
                </div>
                <div style={{ background: '#e8f5e9', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #2e7d32' }}>
                    <small style={{ color: '#2e7d32', fontWeight: 700, display: 'block' }}>🏷️ State-wise Rainfall Records</small>
                    <strong style={{ fontSize: '1.4rem', color: '#1b5e20' }}>{summary.state_records ?? '—'} States</strong>
                </div>
                <div style={{ background: '#ede7f6', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #5e35b1' }}>
                    <small style={{ color: '#5e35b1', fontWeight: 700, display: 'block' }}>🏷️ River Basin Forecast</small>
                    <strong style={{ fontSize: '1.4rem', color: '#4527a0' }}>{summary.basin_sub_basins ?? '—'} Sub-Basins (QPF)</strong>
                </div>
                <div style={{ background: '#fff3e0', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #ff9800' }}>
                    <small style={{ color: '#ef6c00', fontWeight: 700, display: 'block' }}>🏷️ District Warnings</small>
                    <strong style={{ fontSize: '1.05rem' }}>
                        <span style={{ color: WARNING_COLORS.Red }}>🔴 {redCount}</span>{' '}
                        <span style={{ color: WARNING_COLORS.Orange }}>🟠 {orangeCount}</span>{' '}
                        <span style={{ color: '#b5a000' }}>🟡 {yellowCount}</span>{' '}
                        <span style={{ color: WARNING_COLORS.Green }}>🟢 {greenCount}</span>
                    </strong>
                </div>
                <div style={{ background: '#fce4ec', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #d81b60' }}>
                    <small style={{ color: '#c2185b', fontWeight: 700, display: 'block' }}>🏷️ Station Nowcast Alerts</small>
                    <strong style={{ fontSize: '1.4rem', color: '#ad1457' }}>{summary.nowcast_alerts ?? '—'} Active Alerts</strong>
                </div>
                <div style={{ background: '#e0f2f1', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #00897b' }}>
                    <small style={{ color: '#00695c', fontWeight: 700, display: 'block' }}>🏷️ Next Year Prediction ({predictData?.next_year})</small>
                    <strong style={{ fontSize: '1.15rem', color: '#004d40' }}>
                        {predictData?.predicted_annual_rainfall_mm ?? '—'} mm • {predictData?.heavy_rainfall_events_predicted ?? '—'} heavy events
                    </strong>
                </div>
                <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '10px', borderLeft: predictData?.trend === 'increasing' ? '4px solid #d32f2f' : '4px solid #2e7d32' }}>
                    <small style={{ color: '#555', fontWeight: 700, display: 'block' }}>📈 Trend Indicator</small>
                    <strong style={{ fontSize: '1.2rem', color: predictData?.trend === 'increasing' ? '#d32f2f' : '#2e7d32' }}>
                        {predictData?.trend === 'increasing' ? '🔺 Increasing' : '🔻 Decreasing'} ({predictData?.change_percent > 0 ? '+' : ''}{predictData?.change_percent}%)
                    </strong>
                </div>
            </div>
            {/* Main line chart */}
            <div style={{ height: '360px', position: 'relative', marginBottom: '1.5rem' }}>
                <Line data={chartConfig} options={{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw} mm` } },
                    },
                    scales: {
                        y: { beginAtZero: true, title: { display: true, text: 'Rainfall (mm)' } },
                        x: { title: { display: true, text: 'Month' }, ticks: { maxTicksLimit: 16 } },
                    },
                }} />
            </div>

            {/* Risk + SHAP row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                <div style={{ background: '#fafafa', borderRadius: '10px', padding: '1rem', border: '1px solid #eee' }}>
                    <h4 style={{ margin: '0 0 0.6rem', color: '#37474f' }}>🧠 AI Heavy-Rainfall Risk Assessment</h4>
                    <p style={{ margin: '0.2rem 0' }}>
                        Risk Level:{' '}
                        <strong style={{ color: predictData?.risk_color, fontSize: '1.05rem' }}>{predictData?.risk_level}</strong>
                    </p>
                    <p style={{ margin: '0.2rem 0' }}>Peak Forecast: <strong>{predictData?.peak_forecast_month}</strong> ({predictData?.peak_forecast_mm} mm)</p>
                    <p style={{ margin: '0.2rem 0', fontSize: '0.85rem', color: '#777' }}>Model: {predictData?.model_type} • SARIMA AIC: {predictData?.sarima?.aic ?? 'n/a'}</p>
                </div>
                <div style={{ background: '#fafafa', borderRadius: '10px', padding: '1rem', border: '1px solid #eee' }}>
                    <h4 style={{ margin: '0 0 0.6rem', color: '#37474f' }}>🔍 SHAP Feature Influence</h4>
                    {shapEntries.length > 0 ? shapEntries.map(([feat, val]) => (
                        <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                            <span style={{ width: '110px', fontSize: '0.82rem', color: '#555' }}>{feat}</span>
                            <div style={{ flex: 1, background: '#eceff1', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                                <div style={{ width: `${(val / maxShap) * 100}%`, height: '100%', background: 'linear-gradient(90deg,#0288d1,#e65100)' }} />
                            </div>
                            <span style={{ width: '52px', textAlign: 'right', fontSize: '0.78rem', color: '#777' }}>{val}</span>
                        </div>
                    )) : <p style={{ fontSize: '0.85rem', color: '#888' }}>Explainability module loading…</p>}
                </div>
            </div>
        </div>
    );
};

export default RainfallPredictorChart;
