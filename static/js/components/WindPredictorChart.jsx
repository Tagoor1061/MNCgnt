import React, { useEffect, useState, useRef } from 'react';
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement,
    LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, Filler);

const HAZARD_COLORS = { LOW: '#2e7d32', MODERATE: '#fbc02d', HIGH: '#FFA500', EXTREME: '#FF0000' };

const WindPredictorChart = () => {
    const [predictData, setPredictData] = useState(null);
    const [windData, setWindData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [lastRefreshed, setLastRefreshed] = useState(null);
    const intervalRef = useRef(null);

    const fetchData = async () => {
        try {
            const [predRes, windRes] = await Promise.all([
                fetch('/api/predict/wind'),
                fetch('/api/disaster-data/wind'),
            ]);
            setPredictData(await predRes.json());
            setWindData(await windRes.json());
            setLastRefreshed(new Date().toLocaleTimeString());
        } catch (err) {
            console.error('Error fetching wind preparedness data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        try {
            await fetch('/api/disaster-data/wind/refresh', { method: 'POST' });
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
        return <div className="wind-loading">Loading IMD Wind Analytics & AI Hazard Models...</div>;
    }

    /* ---------------- chart data: history + AI trajectory ---------------- */
    const hourlyHistory = predictData?.hourly_history || [];
    const forecastTrajectory = predictData?.forecast_trajectory || [];
    const histLabels = hourlyHistory.map(m => m.time.slice(5, 16));
    const histValues = hourlyHistory.map(m => m.gust_kmph);
    const fcLabels = forecastTrajectory.map(f => f.time.slice(5, 16));
    const fcBlended = forecastTrajectory.map(f => f.blended_gust_kmph);
    const fcArima = forecastTrajectory.map(f => f.arima_gust_kmph);
    const bridgeIdx = Math.max(histLabels.length - 1, 0);

    const chartConfig = {
        labels: [...histLabels, ...fcLabels],
        datasets: [
            {
                label: 'Historical Gust Speed (km/h)',
                data: [...histValues, ...Array(fcLabels.length).fill(null)],
                borderColor: '#00695c',
                backgroundColor: 'rgba(0, 105, 92, 0.15)',
                fill: true, tension: 0.35, pointRadius: 1, borderWidth: 2,
            },
            {
                label: `AI Prediction (${predictData?.gust_model_kind?.includes('ARIMA') ? 'ARIMA' : 'ML'} + Classifier)`,
                data: [...Array(bridgeIdx).fill(null), histValues[bridgeIdx], ...fcBlended],
                borderColor: '#e65100',
                borderDash: [6, 4],
                fill: false, tension: 0.35, pointRadius: 2, borderWidth: 2.5,
            },
            {
                label: 'ARIMA Forecast',
                data: [...Array(bridgeIdx).fill(null), histValues[bridgeIdx], ...fcArima],
                borderColor: '#5e35b1',
                borderDash: [2, 3],
                fill: false, tension: 0.35, pointRadius: 0, borderWidth: 1.5,
            },
        ],
    };

    /* ---------------- badges ---------------- */
    const summary = windData?.summary || {};
    const shapEntries = Object.entries(predictData?.explainability?.shap_feature_importance || {});
    const maxShap = Math.max(...shapEntries.map(([, v]) => v), 0.0001);

    return (
        <div className="wind-preparedness-unit" style={{ background: '#ffffff', padding: '1.8rem', borderRadius: '14px', boxShadow: '0 8px 25px rgba(0,0,0,0.08)', marginBottom: '2rem' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', borderBottom: '2px solid #e0f2f1', paddingBottom: '0.8rem' }}>
                <div>
                    <h2 style={{ margin: 0, color: '#00695c', fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        💨 Wind Preparedness Unit — IMD Analytics & AI Prediction
                    </h2>
                    <small style={{ color: '#666' }}>
                        Connected to IMD District Warnings (codes 4/7/8/14/15/32) & Station Nowcast (Cat4–Cat18)
                        {lastRefreshed && <> • Last updated {lastRefreshed}</>}
                    </small>
                </div>
                <button onClick={handleRefresh} disabled={refreshing}
                    style={{ background: '#00695c', color: '#fff', border: 'none', padding: '0.7rem 1.4rem', borderRadius: '8px', cursor: refreshing ? 'wait' : 'pointer', fontWeight: 700 }}>
                    {refreshing ? '🔄 Refreshing & Retraining...' : '🔄 Manual Refresh & Retrain'}
                </button>
            </div>

            {/* Badges grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '1rem', marginBottom: '1.8rem' }}>
                <div style={{ background: '#e0f2f1', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #00695c' }}>
                    <small style={{ color: '#00695c', fontWeight: 700, display: 'block' }}>🏷️ Current Wind Warnings</small>
                    <strong style={{ fontSize: '1.05rem', color: '#004d40' }}>
                        🔴 {summary.red_warnings ?? 0} 🟠 {summary.orange_warnings ?? 0} 🟡 {summary.yellow_warnings ?? 0} 🟢 {summary.green_warnings ?? 0}
                    </strong>
                </div>
                <div style={{ background: '#e3f2fd', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #1565c0' }}>
                    <small style={{ color: '#1565c0', fontWeight: 700, display: 'block' }}>🏷️ Station-wise Gust Speeds</small>
                    <strong style={{ fontSize: '1.3rem', color: '#0d47a1' }}>{summary.max_gust_kmph ?? '—'} km/h Peak</strong>
                </div>
                <div style={{ background: '#fff3e0', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #ef6c00' }}>
                    <small style={{ color: '#ef6c00', fontWeight: 700, display: 'block' }}>🏷️ District Hazard Zones</small>
                    <strong style={{ fontSize: '1.3rem', color: '#e65100' }}>{summary.hazard_districts ?? '—'} Districts</strong>
                </div>
                <div style={{ background: '#ede7f6', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #5e35b1' }}>
                    <small style={{ color: '#5e35b1', fontWeight: 700, display: 'block' }}>🏷️ Next Year Prediction ({predictData?.next_year})</small>
                    <strong style={{ fontSize: '1.15rem', color: '#4527a0' }}>
                        {predictData?.predicted_severe_events_next_year ?? '—'} severe-wind events
                    </strong>
                </div>
                <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '10px', borderLeft: predictData?.trend === 'increasing' ? '4px solid #d32f2f' : '4px solid #2e7d32' }}>
                    <small style={{ color: '#555', fontWeight: 700, display: 'block' }}>📈 Trend Indicator</small>
                    <strong style={{ fontSize: '1.15rem', color: predictData?.trend === 'increasing' ? '#d32f2f' : '#2e7d32' }}>
                        {predictData?.trend === 'increasing' ? '🔺 Increasing' : '🔻 Decreasing'}
                    </strong>
                </div>
            </div>

            {/* Main line chart */}
            <div style={{ height: '340px', position: 'relative', marginBottom: '1.5rem' }}>
                <Line data={chartConfig} options={{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw} km/h` } },
                    },
                    scales: {
                        y: { beginAtZero: true, title: { display: true, text: 'Gust Speed (km/h)' } },
                        x: { title: { display: true, text: 'Time' }, ticks: { maxTicksLimit: 14 } },
                    },
                }} />
            </div>

            {/* Hazard + SHAP row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                <div style={{ background: '#fafafa', borderRadius: '10px', padding: '1rem', border: '1px solid #eee' }}>
                    <h4 style={{ margin: '0 0 0.6rem', color: '#37474f' }}>🧠 AI Wind Hazard Classification</h4>
                    <p style={{ margin: '0.2rem 0' }}>Current Hazard:{' '}
                        <strong style={{ color: predictData?.current_hazard_color, fontSize: '1.05rem' }}>
                            {predictData?.current_hazard}
                        </strong>
                        {predictData?.hazard_confidence_pct != null && <> ({predictData.hazard_confidence_pct}% conf.)</>}
                    </p>
                    <p style={{ margin: '0.2rem 0' }}>Peak Forecast: <strong>{predictData?.peak_forecast_hour}</strong> — {predictData?.peak_forecast_gust_kmph} km/h ({predictData?.peak_hazard})</p>
                    <p style={{ margin: '0.2rem 0', fontSize: '0.85rem', color: '#777' }}>
                        Classifier: {predictData?.classifier_kind} • Gust model: {predictData?.gust_model_kind}</p>
                </div>
                <div style={{ background: '#fafafa', borderRadius: '10px', padding: '1rem', border: '1px solid #eee' }}>
                    <h4 style={{ margin: '0 0 0.6rem', color: '#37474f' }}>🔍 SHAP Feature Influence</h4>
                    {shapEntries.length > 0 ? shapEntries.map(([feat, val]) => (
                        <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                            <span style={{ width: '110px', fontSize: '0.82rem', color: '#555' }}>{feat}</span>
                            <div style={{ flex: 1, background: '#eceff1', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                                <div style={{ width: `${(val / maxShap) * 100}%`, height: '100%', background: 'linear-gradient(90deg,#00695c,#e65100)' }} />
                            </div>
                            <span style={{ width: '52px', textAlign: 'right', fontSize: '0.78rem', color: '#777' }}>{val}</span>
                        </div>
                    )) : <p style={{ fontSize: '0.85rem', color: '#888' }}>Explainability module loading…</p>}
                </div>
            </div>
        </div>
    );
};

export default WindPredictorChart;
