import React, { useState, useEffect } from 'react';
import axios from 'axios';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { 
  Upload, BarChart3, Cpu, Sparkles, Filter, RefreshCw, 
  Download, ImageDown, CheckCircle2, AlertCircle, Eye, EyeOff, FileText, Sun, Moon
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter, LineChart, Line,
  CartesianGrid
} from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/autoinsight';

// Warm, earthy vintage palette for analytical visualizations & charts
const CHART_VINTAGE_COLORS = [
  '#C85A32', // Warm Terracotta / Rust
  '#2A6F6D', // Deep Vintage Teal
  '#E3A857', // Mustard / Ochre
  '#8F9779', // Sage Green
  '#D48C95', // Dusty Rose
  '#4A6B82', // Slate Blue
  '#D97724', // Burnt Orange
  '#6B5B95'  // Muted Plum / Vintage Violet
];

export default function App() {
  const [theme, setTheme] = useState('dark'); // 'dark' | 'light'
  const [file, setFile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [statusMsg, setStatusMsg] = useState(null);

  // Custom Controls State
  const [visualData, setVisualData] = useState(null);
  const [selectedCols, setSelectedCols] = useState([]);
  const [maxRows, setMaxRows] = useState('');
  const [chartTypeOverrides, setChartTypeOverrides] = useState({});

  // Data Cleaner State
  const [removeDupes, setRemoveDupes] = useState(false);
  const [cleanLogs, setCleanLogs] = useState([]);

  // Machine Learning State
  const [targetCol, setTargetCol] = useState('');
  const [modelResults, setModelResults] = useState(null);
  const [predictionInput, setPredictionInput] = useState({});
  const [predictionOutput, setPredictionOutput] = useState(null);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const isDark = theme === 'dark';

  const isStrictIdentifier = (colName) => {
    if (!colName) return false;
    const lower = colName.toLowerCase().trim();
    return lower === 'id' || lower === 'index' || lower === 'uuid' || lower === 'unnamed: 0' || lower.endsWith('_id');
  };

  const getDataType = (col) => {
    if (!metadata) return 'unknown';
    if (metadata.data_types && metadata.data_types[col]) return metadata.data_types[col];
    if (metadata.dtypes && metadata.dtypes[col]) return metadata.dtypes[col];
    return 'object';
  };

  const resetWorkspace = () => {
    setMetadata(null);
    setSessionId(null);
    setVisualData(null);
    setSelectedCols([]);
    setMaxRows('');
    setChartTypeOverrides({});
    setCleanLogs([]);
    setTargetCol('');
    setModelResults(null);
    setPredictionInput({});
    setPredictionOutput(null);
  };

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    resetWorkspace();
    setFile(selectedFile);
    setLoading(true);
    setStatusMsg(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await axios.post(`${API_BASE}/upload`, formData);
      const data = res.data;
      const meta = data.metadata || data;
      
      setSessionId(data.session_id);
      setMetadata(meta);
      setSelectedCols(meta.columns || []);
      
      let initialCharts = data.visualizations?.charts || data.charts || [];
      setVisualData({ charts: initialCharts });

      setActiveTab('analytics');
      setStatusMsg({ type: 'success', text: 'Dataset uploaded and default visuals generated instantly!' });
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'An unexpected error occurred.';
      setStatusMsg({ type: 'error', text: 'Upload failed: ' + errMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFilter = async () => {
    setLoading(true);
    setStatusMsg(null);

    try {
      const headers = sessionId ? { 'X-Session-ID': sessionId } : {};
      const res = await axios.post(
        `${API_BASE}/visualize/customize`,
        { 
          included_columns: selectedCols, 
          max_rows: maxRows ? parseInt(maxRows, 10) : null 
        },
        { headers }
      );

      setVisualData(res.data.visualizations);
      setStatusMsg({ type: 'success', text: 'Visualizations successfully updated!' });
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'Failed to update charts.';
      setStatusMsg({ type: 'error', text: errMsg });
    } finally {
      setLoading(false);
    }
  };

  const toggleColumn = (col) => {
    if (selectedCols.includes(col)) {
      setSelectedCols(selectedCols.filter(c => c !== col));
    } else {
      setSelectedCols([...selectedCols, col]);
    }
  };

  const handleSelectAll = () => setSelectedCols(metadata?.columns || []);
  const handleDeselectAll = () => setSelectedCols([]);

  const downloadChartImage = (chartId, title) => {
    const chartContainer = document.getElementById(`chart-container-${chartId}`);
    if (!chartContainer) return;

    const svgElement = chartContainer.querySelector('svg');
    if (!svgElement) return;

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      canvas.width = svgElement.clientWidth || 600;
      canvas.height = svgElement.clientHeight || 300;
      ctx.fillStyle = isDark ? '#0a0a0a' : '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);

      const pngUrl = canvas.toDataURL('image/png');
      const downloadLink = document.createElement('a');
      downloadLink.href = pngUrl;
      downloadLink.download = `${title.toLowerCase().replace(/\s+/g, '_')}_chart.png`;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    };

    img.src = url;
  };

  // Export Full Page Dashboard as PDF
  const downloadFullPagePdf = async () => {
    const targetEl = document.getElementById('dashboard-main-content');
    if (!targetEl) return;

    try {
      setLoading(true);
      const canvas = await html2canvas(targetEl, {
        scale: 2,
        backgroundColor: isDark ? '#000000' : '#f8fafc',
        useCORS: true
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`autoinsight_report_${Date.now()}.pdf`);
      setStatusMsg({ type: 'success', text: 'Dashboard report downloaded successfully!' });
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Failed to generate PDF snapshot: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleCleanData = async () => {
    if (!file) return;
    setLoading(true);
    setStatusMsg(null);

    try {
      const headers = sessionId ? { 'X-Session-ID': sessionId } : {};
      const res = await axios.post(
        `${API_BASE}/clean`, 
        { filename: file.name, remove_dup: removeDupes },
        { headers }
      );

      const updatedMetadata = res.data.metadata_after || res.data.metadata || res.data;
      setMetadata(updatedMetadata);
      setCleanLogs(res.data.logs || res.data.cleaning_logs || []);

      if (res.data.visualizations) {
        setVisualData(res.data.visualizations);
      }

      setStatusMsg({ type: 'success', text: 'Data cleaning pipeline executed successfully!' });
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'An unexpected error occurred.';
      setStatusMsg({ type: 'error', text: 'Cleaning failed: ' + errMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleTrainModel = async () => {
    if (!targetCol) return alert('Please select a target column to predict!');
    setLoading(true);
    setStatusMsg(null);
    setPredictionInput({});
    setPredictionOutput(null);

    try {
      const headers = sessionId ? { 'X-Session-ID': sessionId } : {};
      const res = await axios.post(
        `${API_BASE}/train?filename=${encodeURIComponent(file.name)}&target_column=${encodeURIComponent(targetCol)}&model_name=ui_model&source=processed`,
        {},
        { headers }
      );
      setModelResults(res.data.model_results || res.data);
      setStatusMsg({ type: 'success', text: 'Machine Learning model trained successfully!' });
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'An unexpected error occurred.';
      setStatusMsg({ type: 'error', text: 'Training failed: ' + errMsg });
    } finally {
      setLoading(false);
    }
  };

  const handlePredict = async () => {
    setLoading(true);
    setStatusMsg(null);

    try {
      const processedInputs = {};
      Object.keys(predictionInput).forEach((key) => {
        const val = predictionInput[key];
        if (val === '' || val === null || val === undefined) return;
        processedInputs[key] = !isNaN(val) ? Number(val) : val;
      });

      const res = await axios.post(`${API_BASE}/predict/ui_model`, processedInputs);
      setPredictionOutput(res.data.prediction ?? res.data.result);
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'An unexpected error occurred.';
      setStatusMsg({ type: 'error', text: 'Prediction failed: ' + errMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    const url = sessionId 
      ? `${API_BASE}/export?x_session_id=${sessionId}` 
      : `${API_BASE}/export`;
    window.open(url, '_blank');
  };

  return (
    <div className={`min-h-screen flex flex-col font-sans selection:bg-neutral-500/30 transition-colors duration-200 ${
      isDark ? 'bg-black text-neutral-100' : 'bg-slate-50 text-slate-900'
    }`}>
      {/* Header Bar */}
      <header className={`border-b px-8 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50 backdrop-blur-md transition-colors ${
        isDark ? 'border-neutral-800 bg-black/90' : 'border-slate-200 bg-white/90'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg shadow-md transition-colors ${isDark ? 'bg-white text-black' : 'bg-slate-900 text-white'}`}>
            <Sparkles className="w-5 h-5" />
          </div>
          <h1 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
            AutoInsight <span className={`font-normal ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>AI</span>
          </h1>
        </div>

        <nav className={`flex gap-2 p-1.5 rounded-xl border transition-colors ${
          isDark ? 'bg-neutral-900/90 border-neutral-800' : 'bg-slate-100 border-slate-200'
        }`}>
          <NavButton isDark={isDark} active={activeTab === 'upload'} onClick={() => setActiveTab('upload')} icon={Upload} label="Upload" />
          <NavButton isDark={isDark} active={activeTab === 'analytics'} disabled={!metadata} onClick={() => setActiveTab('analytics')} icon={BarChart3} label="Analytics & Charts" />
          <NavButton isDark={isDark} active={activeTab === 'clean'} disabled={!metadata} onClick={() => setActiveTab('clean')} icon={Filter} label="Cleaner" />
          <NavButton isDark={isDark} active={activeTab === 'ml'} disabled={!metadata} onClick={() => setActiveTab('ml')} icon={Cpu} label="Machine Learning" />
        </nav>

        <div className="flex items-center gap-3">
          {/* Light/Dark Toggle Button */}
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-xl border transition-colors flex items-center justify-center ${
              isDark 
                ? 'bg-neutral-900 border-neutral-800 text-amber-400 hover:bg-neutral-800' 
                : 'bg-slate-100 border-slate-200 text-slate-700 hover:bg-slate-200'
            }`}
            title={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Download Dashboard PDF Button */}
          {metadata && (
            <button
              onClick={downloadFullPagePdf}
              disabled={loading}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium transition border shadow-sm ${
                isDark 
                  ? 'bg-neutral-100 hover:bg-white text-black border-neutral-300' 
                  : 'bg-slate-900 hover:bg-slate-800 text-white border-slate-800'
              }`}
            >
              <FileText className="w-4 h-4" /> Download Report PDF
            </button>
          )}
        </div>
      </header>

      {/* Main Workspace Content Area */}
      <main id="dashboard-main-content" className="flex-1 max-w-7xl w-full mx-auto p-8">
        {statusMsg && (
          <div className={`mb-6 p-4 rounded-xl border flex items-center justify-between gap-3 ${
            isDark 
              ? statusMsg.type === 'success' ? 'bg-neutral-900/90 border-neutral-700 text-white' : 'bg-neutral-900/90 border-neutral-800 text-neutral-300'
              : statusMsg.type === 'success' ? 'bg-slate-100 border-slate-300 text-slate-900' : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}>
            <div className="flex items-center gap-3">
              {statusMsg.type === 'success' ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> : <AlertCircle className="w-5 h-5 flex-shrink-0" />}
              <span className="text-sm font-medium">{statusMsg.text}</span>
            </div>
            <button onClick={() => setStatusMsg(null)} className="text-xs opacity-60 hover:opacity-100">Dismiss</button>
          </div>
        )}

        {/* VIEW 1: UPLOAD */}
        {activeTab === 'upload' && (
          <div className={`flex flex-col items-center justify-center border border-dashed rounded-2xl p-16 transition my-12 ${
            isDark 
              ? 'border-neutral-800 hover:border-neutral-500 bg-neutral-950/50' 
              : 'border-slate-300 hover:border-slate-400 bg-white'
          }`}>
            <div className={`p-4 rounded-full border mb-4 ${isDark ? 'bg-neutral-900 border-neutral-800' : 'bg-slate-100 border-slate-200'}`}>
              <Upload className={`w-8 h-8 animate-pulse ${isDark ? 'text-white' : 'text-slate-800'}`} />
            </div>
            <h2 className={`text-2xl font-semibold mb-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>Upload Dataset</h2>
            <p className={`text-sm mb-6 ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>Supports CSV, XLS, and XLSX files with unlimited rows & columns</p>
            <label className={`cursor-pointer px-6 py-3 rounded-xl font-medium transition shadow-sm ${
              isDark ? 'bg-white hover:bg-neutral-200 text-black' : 'bg-slate-900 hover:bg-slate-800 text-white'
            }`}>
              {loading ? 'Processing Dataset...' : 'Browse File'}
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>
        )}

        {/* VIEW 2: ANALYTICS & CHARTS */}
        {activeTab === 'analytics' && metadata && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <MetricCard isDark={isDark} label="Total Rows" val={metadata.num_rows ?? metadata.total_rows ?? 0} />
              <MetricCard isDark={isDark} label="Total Columns" val={metadata.num_cols ?? metadata.total_cols ?? 0} />
              <MetricCard isDark={isDark} label="Duplicate Rows" val={metadata.duplicate_rows ?? metadata.duplicates ?? 0} />
            </div>

            {/* Custom Interactive Controls */}
            <div className={`border p-6 rounded-2xl space-y-4 transition-colors ${
              isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
            }`}>
              <div className="flex items-center justify-between">
                <h3 className={`text-xs font-semibold uppercase tracking-widest ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>
                  Interactive Header & Data Filtering
                </h3>
                <div className="flex items-center gap-3 text-xs">
                  <button onClick={handleSelectAll} className={`font-medium hover:underline ${isDark ? 'text-white' : 'text-slate-900'}`}>Select All</button>
                  <span className={isDark ? 'text-neutral-700' : 'text-slate-300'}>|</span>
                  <button onClick={handleDeselectAll} className={isDark ? 'text-neutral-400 hover:text-white' : 'text-slate-500 hover:text-slate-900'}>Deselect All</button>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2">
                {metadata.columns?.map((col) => {
                  const isSelected = selectedCols.includes(col);
                  return (
                    <button
                      key={col}
                      onClick={() => toggleColumn(col)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                        isSelected 
                          ? isDark ? 'bg-white text-black border-white' : 'bg-slate-900 text-white border-slate-900'
                          : isDark ? 'bg-black border-neutral-800 text-neutral-400 hover:border-neutral-700' : 'bg-slate-100 border-slate-200 text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      {isSelected ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                      {col}
                    </button>
                  );
                })}
              </div>

              <div className={`flex flex-wrap items-center justify-between pt-3 border-t gap-4 ${isDark ? 'border-neutral-800' : 'border-slate-200'}`}>
                <div className="flex items-center gap-3">
                  <span className={`text-xs ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>Limit Rows Sample:</span>
                  <input
                    type="number"
                    placeholder="All Rows"
                    value={maxRows}
                    onChange={(e) => setMaxRows(e.target.value)}
                    className={`w-32 rounded-lg px-3 py-1.5 text-xs focus:outline-none border transition-colors ${
                      isDark 
                        ? 'bg-black border-neutral-800 text-white focus:border-neutral-500' 
                        : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-slate-400'
                    }`}
                  />
                </div>

                <button
                  onClick={handleApplyFilter}
                  disabled={loading}
                  className={`px-5 py-2 rounded-xl text-xs font-medium transition flex items-center gap-2 shadow-sm ${
                    isDark ? 'bg-white hover:bg-neutral-200 text-black' : 'bg-slate-900 hover:bg-slate-800 text-white'
                  }`}
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Update Visuals
                </button>
              </div>
            </div>

            {/* VINTAGE VISUALIZATIONS */}
            {visualData && visualData.charts && visualData.charts.length > 0 ? (
              <div>
                <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-slate-900'}`}>Analytical Visualizations</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {visualData.charts.map((chart, chartIdx) => {
                    const currentType = chartTypeOverrides[chart.id] || chart.type;
                    const xAxisKey = chart.x_axis || 'name';
                    const yAxisKey = chart.y_axis || 'count' || 'value' || 'frequency';
                    const primaryChartColor = CHART_VINTAGE_COLORS[chartIdx % CHART_VINTAGE_COLORS.length];

                    const normalizedScatterData = currentType === 'scatter' 
                      ? chart.data.map(item => ({
                          x: item.x ?? item[xAxisKey],
                          y: item.y ?? item[yAxisKey]
                        }))
                      : chart.data;

                    return (
                      <div key={chart.id} className={`border p-5 rounded-2xl flex flex-col justify-between transition-colors ${
                        isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
                      }`}>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className={`text-sm font-medium ${isDark ? 'text-neutral-200' : 'text-slate-800'}`}>{chart.title}</h4>
                          <div className="flex items-center gap-2">
                            {/* Live Chart Type Override Selector */}
                            {currentType !== 'boxplot' && (
                              <select
                                value={currentType}
                                onChange={(e) => setChartTypeOverrides({ ...chartTypeOverrides, [chart.id]: e.target.value })}
                                className={`text-xs rounded-lg px-2.5 py-1 focus:outline-none border transition-colors ${
                                  isDark 
                                    ? 'bg-black border-neutral-800 text-neutral-300 focus:border-neutral-500' 
                                    : 'bg-slate-100 border-slate-300 text-slate-700 focus:border-slate-400'
                                }`}
                              >
                                <option value="bar">Bar Chart</option>
                                <option value="line">Line Graph</option>
                                <option value="donut">Donut / Pie</option>
                                <option value="scatter">Scatter Plot</option>
                              </select>
                            )}

                            {/* Download PNG Button */}
                            <button
                              onClick={() => downloadChartImage(chart.id, chart.title)}
                              title="Download Chart PNG"
                              className={`p-1.5 rounded-lg border transition ${
                                isDark 
                                  ? 'bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border-neutral-800' 
                                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
                              }`}
                            >
                              <ImageDown className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        <div id={`chart-container-${chart.id}`}>
                          {(currentType === 'bar' || currentType === 'histogram') && (
                            <ResponsiveContainer width="100%" height={240}>
                              <BarChart data={chart.data} margin={{ bottom: 25 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#262626' : '#e2e8f0'} />
                                <XAxis 
                                  dataKey={xAxisKey} 
                                  stroke={isDark ? '#737373' : '#64748b'} 
                                  tick={{ fontSize: 11 }}
                                  interval={0}
                                  angle={-25}
                                  textAnchor="end"
                                />
                                <YAxis stroke={isDark ? '#737373' : '#64748b'} tick={{ fontSize: 11 }} />
                                <Tooltip contentStyle={{ 
                                  backgroundColor: isDark ? '#0a0a0a' : '#ffffff', 
                                  borderColor: isDark ? '#262626' : '#cbd5e1', 
                                  borderRadius: '8px', 
                                  color: isDark ? '#fff' : '#0f172a' 
                                }} />
                                <Bar dataKey={yAxisKey} fill={primaryChartColor} radius={[4, 4, 0, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          )}

                          {currentType === 'donut' && (
                            <ResponsiveContainer width="100%" height={240}>
                              <PieChart>
                                <Tooltip contentStyle={{ 
                                  backgroundColor: isDark ? '#0a0a0a' : '#ffffff', 
                                  borderColor: isDark ? '#262626' : '#cbd5e1', 
                                  borderRadius: '8px', 
                                  color: isDark ? '#fff' : '#0f172a' 
                                }} />
                                <Pie data={chart.data} dataKey={yAxisKey} nameKey={xAxisKey} cx="50%" cy="50%" innerRadius={45} outerRadius={75}>
                                  {chart.data.map((entry, idx) => (
                                    <Cell key={`cell-${idx}`} fill={CHART_VINTAGE_COLORS[idx % CHART_VINTAGE_COLORS.length]} />
                                  ))}
                                </Pie>
                              </PieChart>
                            </ResponsiveContainer>
                          )}

                          {currentType === 'scatter' && (
                            <ResponsiveContainer width="100%" height={240}>
                              <ScatterChart>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#262626' : '#e2e8f0'} />
                                <XAxis dataKey="x" stroke={isDark ? '#737373' : '#64748b'} name={chart.x_axis || 'X'} tick={{ fontSize: 11 }} />
                                <YAxis dataKey="y" stroke={isDark ? '#737373' : '#64748b'} name={chart.y_axis || 'Y'} tick={{ fontSize: 11 }} />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ 
                                  backgroundColor: isDark ? '#0a0a0a' : '#ffffff', 
                                  borderColor: isDark ? '#262626' : '#cbd5e1', 
                                  borderRadius: '8px', 
                                  color: isDark ? '#fff' : '#0f172a' 
                                }} />
                                <Scatter data={normalizedScatterData} fill={primaryChartColor} />
                              </ScatterChart>
                            </ResponsiveContainer>
                          )}

                          {currentType === 'line' && (
                            <ResponsiveContainer width="100%" height={240}>
                              <LineChart data={chart.data} margin={{ bottom: 25 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#262626' : '#e2e8f0'} />
                                <XAxis dataKey={xAxisKey} stroke={isDark ? '#737373' : '#64748b'} tick={{ fontSize: 11 }} interval={0} angle={-25} textAnchor="end" />
                                <YAxis stroke={isDark ? '#737373' : '#64748b'} tick={{ fontSize: 11 }} />
                                <Tooltip contentStyle={{ 
                                  backgroundColor: isDark ? '#0a0a0a' : '#ffffff', 
                                  borderColor: isDark ? '#262626' : '#cbd5e1', 
                                  borderRadius: '8px', 
                                  color: isDark ? '#fff' : '#0f172a' 
                                }} />
                                <Line type="monotone" dataKey={yAxisKey} stroke={primaryChartColor} strokeWidth={2.5} dot={{ fill: primaryChartColor }} />
                              </LineChart>
                            </ResponsiveContainer>
                          )}

                          {currentType === 'boxplot' && chart.data[0] && (
                            <div className="grid grid-cols-3 gap-3 pt-2">
                              <BoxMetric isDark={isDark} label="Min" val={chart.data[0].min} />
                              <BoxMetric isDark={isDark} label="Q1 (25%)" val={chart.data[0].q1} />
                              <BoxMetric isDark={isDark} label="Median" val={chart.data[0].median} />
                              <BoxMetric isDark={isDark} label="Q3 (75%)" val={chart.data[0].q3} />
                              <BoxMetric isDark={isDark} label="Max" val={chart.data[0].max} />
                              <BoxMetric isDark={isDark} label="Outliers" val={chart.data[0].outliers_count} isHighlight />
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className={`border rounded-2xl p-8 text-center ${
                isDark ? 'bg-neutral-950 border-neutral-800 text-neutral-400' : 'bg-white border-slate-200 text-slate-500'
              }`}>
                No charts generated by the engine for this selection. Try enabling more columns above.
              </div>
            )}

            <div className={`border p-6 rounded-2xl transition-colors ${
              isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
            }`}>
              <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-slate-900'}`}>Dataset Columns & Dtypes</h3>
              <div className={`divide-y ${isDark ? 'divide-neutral-900' : 'divide-slate-100'}`}>
                {metadata.columns?.map((col) => (
                  <div key={col} className="py-3 flex justify-between items-center">
                    <span className={`font-medium ${isDark ? 'text-neutral-300' : 'text-slate-700'}`}>{col}</span>
                    <div className="flex items-center gap-2">
                      {isStrictIdentifier(col) && (
                        <span className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded border ${
                          isDark ? 'bg-neutral-900 text-neutral-400 border-neutral-800' : 'bg-slate-100 text-slate-500 border-slate-200'
                        }`}>
                          System Identifier
                        </span>
                      )}
                      <span className={`text-xs font-mono px-3 py-1 rounded-full border ${
                        isDark ? 'bg-black border-neutral-800 text-neutral-300' : 'bg-slate-100 border-slate-200 text-slate-700'
                      }`}>
                        {getDataType(col)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* VIEW 3: CLEANER */}
        {activeTab === 'clean' && metadata && (
          <div className="space-y-6">
            <div className={`border p-6 rounded-2xl space-y-4 transition-colors ${
              isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
            }`}>
              <h3 className={`text-lg font-medium flex items-center gap-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                <Filter className={`w-5 h-5 ${isDark ? 'text-neutral-300' : 'text-slate-600'}`} /> Data Cleaning Rules
              </h3>
              <div className="flex items-center gap-4 pt-2">
                <label className={`flex items-center gap-3 cursor-pointer ${isDark ? 'text-neutral-300' : 'text-slate-700'}`}>
                  <input
                    type="checkbox"
                    checked={removeDupes}
                    onChange={(e) => setRemoveDupes(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-400 focus:ring-slate-400"
                  />
                  <span>Remove Duplicate Rows</span>
                </label>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  onClick={handleCleanData}
                  disabled={loading}
                  className={`px-6 py-2.5 rounded-xl font-medium transition flex items-center gap-2 shadow-sm ${
                    isDark ? 'bg-white hover:bg-neutral-200 text-black' : 'bg-slate-900 hover:bg-slate-800 text-white'
                  }`}
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  {loading ? 'Executing Pipeline...' : 'Run Cleaning Pipeline'}
                </button>

                <button
                  onClick={handleExport}
                  className={`px-6 py-2.5 rounded-xl font-medium transition flex items-center gap-2 border ${
                    isDark ? 'bg-neutral-900 hover:bg-neutral-800 text-white border-neutral-800' : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300'
                  }`}
                >
                  <Download className="w-4 h-4" /> Export Cleaned CSV
                </button>
              </div>
            </div>

            {cleanLogs.length > 0 && (
              <div className={`border p-6 rounded-2xl transition-colors ${
                isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
              }`}>
                <h4 className={`text-xs font-semibold tracking-wider uppercase mb-3 ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>Execution Logs</h4>
                <ul className={`space-y-2 font-mono text-xs ${isDark ? 'text-neutral-300' : 'text-slate-700'}`}>
                  {cleanLogs.map((log, index) => (
                    <li key={index} className={`p-2.5 rounded-lg border ${
                      isDark ? 'bg-black border-neutral-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      ✓ {log}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* VIEW 4: MACHINE LEARNING */}
        {activeTab === 'ml' && metadata && (
          <div className="space-y-8">
            <div className={`border p-6 rounded-2xl space-y-4 transition-colors ${
              isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
            }`}>
              <h3 className={`text-lg font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>Configure Automated ML Model</h3>
              <div className="flex gap-4">
                <select
                  value={targetCol}
                  onChange={(e) => setTargetCol(e.target.value)}
                  className={`border rounded-xl px-4 py-2.5 flex-1 focus:outline-none transition-colors ${
                    isDark ? 'bg-black border-neutral-800 text-white focus:border-neutral-500' : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-slate-400'
                  }`}
                >
                  <option value="">-- Select Column to Predict --</option>
                  {metadata.columns?.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleTrainModel}
                  disabled={loading}
                  className={`px-6 py-2.5 rounded-xl font-medium transition shadow-sm ${
                    isDark ? 'bg-white hover:bg-neutral-200 text-black' : 'bg-slate-900 hover:bg-slate-800 text-white'
                  }`}
                >
                  {loading ? 'Training...' : 'Train Model'}
                </button>
              </div>
            </div>

            {modelResults && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className={`border p-6 rounded-2xl space-y-4 transition-colors ${
                  isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
                }`}>
                  <h4 className={`font-medium ${isDark ? 'text-neutral-200' : 'text-slate-800'}`}>Model Performance</h4>
                  <div className={`p-4 border rounded-xl ${
                    isDark ? 'bg-black border-neutral-800' : 'bg-slate-50 border-slate-200'
                  }`}>
                    <p className={`text-xs uppercase tracking-wider ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>
                      {modelResults.metrics?.metric_name || 'Evaluation Metric'}
                    </p>
                    <p className={`text-3xl font-bold mt-1 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                      {modelResults.metrics?.metric_value ?? 'N/A'}
                    </p>
                  </div>

                  <h5 className={`font-medium text-xs uppercase tracking-wider pt-2 ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>Feature Importance</h5>
                  <div className="space-y-3">
                    {modelResults.feature_importances?.map((item, idx) => (
                      <div key={item.feature} className="flex items-center gap-4">
                        <span className={`w-28 text-xs truncate ${isDark ? 'text-neutral-300' : 'text-slate-700'}`}>{item.feature}</span>
                        <div className={`flex-1 h-2 rounded-full overflow-hidden border ${
                          isDark ? 'bg-black border-neutral-800' : 'bg-slate-100 border-slate-200'
                        }`}>
                          <div
                            className="h-full rounded-full"
                            style={{ 
                              width: `${(item.importance || 0) * 100}%`,
                              backgroundColor: CHART_VINTAGE_COLORS[idx % CHART_VINTAGE_COLORS.length]
                            }}
                          />
                        </div>
                        <span className={`text-xs font-mono w-12 text-right ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>
                          {((item.importance || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className={`border p-6 rounded-2xl space-y-4 transition-colors ${
                  isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
                }`}>
                  <h4 className={`font-medium ${isDark ? 'text-neutral-200' : 'text-slate-800'}`}>Run Inference</h4>
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                    {metadata.columns
                      ?.filter((c) => c !== targetCol && !isStrictIdentifier(c))
                      .map((col) => (
                        <div key={col}>
                          <label className={`text-xs block mb-1 ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>{col}</label>
                          <input
                            type="text"
                            placeholder={`Enter ${col}`}
                            value={predictionInput[col] || ''}
                            onChange={(e) =>
                              setPredictionInput({ ...predictionInput, [col]: e.target.value })
                            }
                            className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none transition-colors ${
                              isDark 
                                ? 'bg-black border-neutral-800 text-white focus:border-neutral-500' 
                                : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-slate-400'
                            }`}
                          />
                        </div>
                      ))}
                  </div>

                  <button
                    onClick={handlePredict}
                    disabled={loading}
                    className={`w-full py-2.5 rounded-xl text-sm font-medium transition shadow-sm ${
                      isDark ? 'bg-white hover:bg-neutral-200 text-black' : 'bg-slate-900 hover:bg-slate-800 text-white'
                    }`}
                  >
                    {loading ? 'Executing...' : 'Run Prediction'}
                  </button>

                  {predictionOutput !== null && (
                    <div className={`mt-4 p-4 border rounded-xl text-center ${
                      isDark ? 'bg-black border-neutral-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <p className={`text-xs font-medium ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>Predicted Result</p>
                      <p className={`text-2xl font-bold mt-1 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        {typeof predictionOutput === 'number'
                          ? predictionOutput.toLocaleString()
                          : predictionOutput}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function NavButton({ isDark, active, disabled, onClick, icon: Icon, label }) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
        disabled
          ? 'opacity-30 cursor-not-allowed'
          : active
          ? isDark ? 'bg-white text-black font-semibold shadow-sm' : 'bg-white text-slate-900 font-semibold shadow-sm'
          : isDark ? 'text-neutral-400 hover:text-white hover:bg-neutral-800/60' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
      }`}
    >
      <Icon className="w-4 h-4" /> {label}
    </button>
  );
}

function MetricCard({ isDark, label, val }) {
  return (
    <div className={`border p-6 rounded-2xl transition-colors ${
      isDark ? 'bg-neutral-950 border-neutral-800' : 'bg-white border-slate-200 shadow-sm'
    }`}>
      <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${isDark ? 'text-neutral-400' : 'text-slate-500'}`}>{label}</p>
      <p className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{val}</p>
    </div>
  );
}

function BoxMetric({ isDark, label, val, isHighlight }) {
  return (
    <div className={`p-2.5 rounded-lg border text-center ${
      isDark ? 'bg-black border-neutral-800' : 'bg-slate-50 border-slate-200'
    }`}>
      <p className={`text-[10px] uppercase ${isDark ? 'text-neutral-500' : 'text-slate-500'}`}>{label}</p>
      <p className={`text-xs font-bold font-mono mt-0.5 ${
        isHighlight && val > 0 
          ? isDark ? 'text-white' : 'text-slate-900' 
          : isDark ? 'text-neutral-300' : 'text-slate-700'
      }`}>
        {val ?? 'N/A'}
      </p>
    </div>
  );
}