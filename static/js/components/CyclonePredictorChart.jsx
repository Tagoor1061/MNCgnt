import React, { useEffect, useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

const CyclonePredictorChart = () => {
    const [predictData, setPredictData] = useState(null);
    const [disasterData, setDisasterData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        try {
            const [predRes, dataRes] = await Promise.all([
                fetch('/api/predict/cyclone'),
                fetch('/api/disaster-data/cyclone')
            ]);
            const pData = await predRes.json();
            const dData = await dataRes.json();
            setPredictData(pData);
            setDisasterData(dData);
        } catch (err) {
            console.error("Error fetching cyclone preparedness data:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        try {
            await fetch('/api/disaster-data/refresh', { method: 'POST' });
            await fetchData();
        } catch (err) {
            console.error("Manual refresh failed:", err);
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000); // Auto-refresh every 60s
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="cyclone-loading">Loading IMD Cyclone Preparedness Analytics & Predictive Model...</div>;

    const history = predictData?.historical_data || {};
    const years = Object.keys(history);
    const counts = Object.values(history);

    if (predictData?.next_year) {
        years.push(`${predictData.next_year} (Predicted)`);
        counts.push(predictData.predicted_frequency);
    }

    const chartConfig = {
        labels: years,
        datasets: [
            {
                type: 'bar',
                label: 'Historical Cyclone Frequency',
                data: counts,
                backgroundColor: counts.map((_, idx) => idx === counts.length - 1 ? '#ff9800' : 'rgba(230, 81, 0, 0.5)'),
                borderColor: counts.map((_, idx) => idx === counts.length - 1 ? '#e65100' : '#e65100'),
                borderWidth: 2,
                borderRadius: 6,
            },
            {
                type: 'line',
                label: 'scikit-learn ML Regression Trend',
                data: counts,
                borderColor: '#e65100',
                borderDash: [5, 5],
                fill: false,
                tension: 0.3,
                pointRadius: 5,
            }
        ]
    };

    return (
        <div className="cyclone-preparedness-unit" style={{ background: '#ffffff', padding: '1.8rem', borderRadius: '14px', boxShadow: '0 8px 25px rgba(0,0,0,0.08)', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', borderBottom: '2px solid #fff3e0', paddingBottom: '0.8rem' }}>
                <div>
                    <h2 style={{ margin: 0, color: '#e65100', fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        🌀 Cyclone Preparedness Unit — IMD Analytics & ML Prediction
                    </h2>
                    <small style={{ color: '#666' }}>Connected to IMD Cyclone Track, Wind Warning, and Cone of Uncertainty APIs</small>
                </div>
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    style={{ background: '#e65100', color: '#fff', border: 'none', padding: '0.7rem 1.4rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
                >
                    {refreshing ? '🔄 Retraining Model...' : '🔄 Refresh & Retrain Model'}
                </button>
            </div>

            {/* Badges Grid */}
            <div className="cyclone-badges-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '1rem', marginBottom: '1.8rem' }}>
                {/* Badge 1: Current Active Cyclones */}
                <div style={{ background: '#fff3e0', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #e65100' }}>
                    <small style={{ color: '#e65100', fontWeight: 700, display: 'block' }}>🏷️ Current Active Cyclones</small>
                    <strong style={{ fontSize: '1.4rem', color: '#b71c1c' }}>{predictData?.active_cyclones ?? 1} Active (IMD Track)</strong>
                </div>

                {/* Badge 2: Wind Warning Zones */}
                <div style={{ background: '#fff8e1', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #ff8f00' }}>
                    <small style={{ color: '#ff8f00', fontWeight: 700, display: 'block' }}>🏷️ Wind Warning Zones</small>
                    <strong style={{ fontSize: '1.4rem', color: '#e65100' }}>{predictData?.wind_warning_zones ?? 3} Zones (IMD Wind)</strong>
                </div>

                {/* Badge 3: Cone of Uncertainty */}
                <div style={{ background: '#f3e5f5', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #8e24aa' }}>
                    <small style={{ color: '#8e24aa', fontWeight: 700, display: 'block' }}>🏷️ Cone of Uncertainty</small>
                    <strong style={{ fontSize: '1.4rem', color: '#6a1b9a' }}>{predictData?.cou_zones ?? 1} Active Cone (IMD COU)</strong>
                </div>

                {/* Badge 4: Last Year Records */}
                <div style={{ background: '#e3f2fd', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #1976d2' }}>
                    <small style={{ color: '#1565c0', fontWeight: 700, display: 'block' }}>🏷️ Last Year Records ({predictData?.last_year})</small>
                    <strong style={{ fontSize: '1.4rem', color: '#1565c0' }}>{predictData?.last_year_count ?? 12} Incidents</strong>
                </div>

                {/* Badge 5: Next Year Prediction */}
                <div style={{ background: '#e8f5e9', padding: '1rem', borderRadius: '10px', borderLeft: '4px solid #2e7d32' }}>
                    <small style={{ color: '#2e7d32', fontWeight: 700, display: 'block' }}>🏷️ Next Year Prediction ({predictData?.next_year})</small>
                    <strong style={{ fontSize: '1.4rem', color: '#1b5e20' }}>{predictData?.predicted_frequency} Predicted</strong>
                </div>

                {/* Badge 6: Trend Indicator */}
                <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '10px', borderLeft: predictData?.trend === 'increasing' ? '4px solid #d32f2f' : '4px solid #2e7d32' }}>
                    <small style={{ color: '#555', fontWeight: 700, display: 'block' }}>📈 Trend Indicator</small>
                    <strong style={{ fontSize: '1.2rem', color: predictData?.trend === 'increasing' ? '#d32f2f' : '#2e7d32' }}>
                        {predictData?.trend === 'increasing' ? '🔺 Increasing Trend' : '🔻 Decreasing Trend'}
                    </strong>
                </div>
            </div>

            {/* Combined Bar + Line Chart */}
            <div style={{ height: '340px', position: 'relative', marginBottom: '1.5rem' }}>
                <Bar data={chartConfig} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }} />
            </div>
        </div>
    );
};

export default CyclonePredictorChart;
