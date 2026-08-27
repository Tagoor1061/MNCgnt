import React, { useEffect, useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

const DisasterPredictorChart = ({ disasterType = 'earthquake' }) => {
    const [chartData, setChartData] = useState(null);
    const [predictionInfo, setPredictionInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/predict/${disasterType}`);
            const data = await res.json();

            setPredictionInfo(data);

            const history = data.historical_data || {};
            const years = Object.keys(history);
            const counts = Object.values(history);

            years.push(`${data.next_year} (Predicted)`);
            counts.push(data.predicted_frequency);

            const backgroundColors = counts.map((_, idx) => idx === counts.length - 1 ? '#ff9800' : 'rgba(25, 118, 210, 0.5)');
            const borderColors = counts.map((_, idx) => idx === counts.length - 1 ? '#e65100' : '#1565c0');

            setChartData({
                labels: years,
                datasets: [
                    {
                        type: 'bar',
                        label: `${disasterType.toUpperCase()} Annual Frequency`,
                        data: counts,
                        backgroundColor: backgroundColors,
                        borderColor: borderColors,
                        borderWidth: 2,
                    },
                    {
                        type: 'line',
                        label: 'ML Linear Regression Trend',
                        data: counts,
                        borderColor: '#1565c0',
                        borderDash: [5, 5],
                        fill: false,
                    }
                ]
            });
        } catch (err) {
            console.error("Error fetching disaster predictions:", err);
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
    }, [disasterType]);

    if (loading) return <div>Loading disaster frequency predictive analytics...</div>;

    return (
        <div className="disaster-react-chart-container" style={{ background: '#fff', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, color: '#1565c0' }}>{disasterType.toUpperCase()} - Historical Trends & ML Prediction</h3>
                <button onClick={handleRefresh} disabled={refreshing} style={{ background: '#1976d2', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}>
                    {refreshing ? '🔄 Retraining Model...' : '🔄 Refresh & Retrain Model'}
                </button>
            </div>

            <div className="stats-badges-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{ background: '#f0f4f8', padding: '0.8rem 1rem', borderRadius: '8px', borderLeft: '4px solid #00838f' }}>
                    <small style={{ color: '#666', fontWeight: 600 }}>Last Hour Records (USGS Live)</small>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#00838f' }}>{predictionInfo?.last_hour_count ?? 0} events</div>
                </div>
                <div style={{ background: '#f0f4f8', padding: '0.8rem 1rem', borderRadius: '8px', borderLeft: '4px solid #1976d2' }}>
                    <small style={{ color: '#666', fontWeight: 600 }}>Last Year ({predictionInfo?.last_year})</small>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#1976d2' }}>{predictionInfo?.last_year_count} incidents</div>
                </div>
                <div style={{ background: '#fff3e0', padding: '0.8rem 1rem', borderRadius: '8px', borderLeft: '4px solid #e65100' }}>
                    <small style={{ color: '#666', fontWeight: 600 }}>Next Year Prediction ({predictionInfo?.next_year})</small>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#e65100' }}>{predictionInfo?.predicted_frequency} predicted</div>
                </div>
                <div style={{ background: '#f0f4f8', padding: '0.8rem 1rem', borderRadius: '8px', borderLeft: predictionInfo?.trend === 'increasing' ? '4px solid #d32f2f' : '4px solid #2e7d32' }}>
                    <small style={{ color: '#666', fontWeight: 600 }}>Predicted Trend</small>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: predictionInfo?.trend === 'increasing' ? '#d32f2f' : '#2e7d32', textTransform: 'capitalize' }}>
                        {predictionInfo?.trend === 'increasing' ? '📈 Increasing' : '📉 Decreasing'}
                    </div>
                </div>
            </div>

            <div style={{ height: '320px', position: 'relative' }}>
                {chartData && <Bar data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />}
            </div>
        </div>
    );
};

export default DisasterPredictorChart;
