import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter, LineChart, Line,
  CartesianGrid, Legend
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

export default function DataVisualizer({ filename, source = 'processed' }) {
  const [visualData, setVisualData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!filename) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetch(`http://localhost:8000/api/visualize/${filename}?source=${source}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch visual insights.');
        return res.json();
      })
      .then((data) => {
        if (isMounted) {
          setVisualData(data.visualizations);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [filename, source]);

  if (loading) return <div style={{ padding: 20 }}>Loading dynamic visualizations...</div>;
  if (error) return <div style={{ color: 'red', padding: 20 }}>Error: {error}</div>;
  if (!visualData || !visualData.charts || !visualData.charts.length) {
    return <div style={{ padding: 20 }}>No visualization data available.</div>;
  }

  return (
    <div style={{ padding: 20, maxWidth: 1200, margin: '0 auto' }}>
      <h2>Data Insights & Visuals</h2>

      {/* Grid Layout for Dashboard Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '20px' }}>
        
        {visualData.charts.map((chart) => (
          <div 
            key={chart.id} 
            style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px', 
              padding: '16px', 
              backgroundColor: '#ffffff',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}
          >
            <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>{chart.title}</h4>

            {/* --- BAR / HISTOGRAM / MISSING DATA --- */}
            {(chart.type === 'bar' || chart.type === 'histogram') && (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chart.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={chart.x_axis} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey={chart.y_axis} fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            )}

            {/* --- DONUT / PIE CHARTS --- */}
            {chart.type === 'donut' && (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Tooltip />
                  <Legend />
                  <Pie
                    data={chart.data}
                    dataKey={chart.y_axis}
                    nameKey={chart.x_axis}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                  >
                    {chart.data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            )}

            {/* --- SCATTER PLOTS --- */}
            {chart.type === 'scatter' && (
              <ResponsiveContainer width="100%" height={250}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" name={chart.x_axis} />
                  <YAxis dataKey="y" name={chart.y_axis} />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter data={chart.data} fill="#00C49F" />
                </ScatterChart>
              </ResponsiveContainer>
            )}

            {/* --- TIME-SERIES LINE CHARTS --- */}
            {chart.type === 'line' && (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chart.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={chart.x_axis} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey={chart.y_axis} stroke="#FF8042" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}

            {/* --- BOX PLOT METRICS CARD --- */}
            {chart.type === 'boxplot' && chart.data[0] && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', paddingTop: '10px' }}>
                <MetricBox label="Min" val={chart.data[0].min} />
                <MetricBox label="Q1 (25%)" val={chart.data[0].q1} />
                <MetricBox label="Median" val={chart.data[0].median} />
                <MetricBox label="Q3 (75%)" val={chart.data[0].q3} />
                <MetricBox label="Max" val={chart.data[0].max} />
                <MetricBox label="Outliers" val={chart.data[0].outliers_count} isBadge />
              </div>
            )}

            {/* --- FALLBACK FOR UNHANDLED TYPES --- */}
            {!['bar', 'histogram', 'donut', 'scatter', 'line', 'boxplot'].includes(chart.type) && (
              <div style={{ padding: '20px', color: '#888', textAlign: 'center' }}>
                Unsupported visual format: <code>{chart.type}</code>
              </div>
            )}

          </div>
        ))}

      </div>
    </div>
  );
}

// Sub-component for Box Plot summaries
function MetricBox({ label, val, isBadge }) {
  const formattedVal = (typeof val === 'number' && !Number.isInteger(val)) 
    ? val.toFixed(2) 
    : val;

  return (
    <div style={{ backgroundColor: '#f9f9f9', padding: '8px', borderRadius: '4px', textAlign: 'center' }}>
      <span style={{ fontSize: '11px', color: '#666', display: 'block' }}>{label}</span>
      <strong style={{ fontSize: '14px', color: isBadge && val > 0 ? '#d9534f' : '#333' }}>
        {formattedVal !== null && formattedVal !== undefined ? formattedVal : 'N/A'}
      </strong>
    </div>
  );
}