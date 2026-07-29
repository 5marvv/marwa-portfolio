let chartInstance = null;

/**
 * Constructs the correct API endpoint URL regardless of route context.
 * Handles root (/), proxy subpaths (/api/ai-analytics), and extra trailing slashes.
 */
function getEndpoint(path) {
    const pathname = window.location.pathname;
    
    // Check if running under proxy path like /api/ai-analytics
    const match = pathname.match(/^(\/api\/[^\/]+)/);
    
    if (match) {
        const servicePrefix = match[1]; // e.g., "/api/ai-analytics"
        return `${servicePrefix}/api/${path.replace(/^\//, '')}`;
    }
    
    return `/api/${path.replace(/^\//, '')}`;
}

document.addEventListener("DOMContentLoaded", () => {
    fetchKPIs();
    fetchChartData();
    fetchTableData();

    // Prevent form submission refresh if input is inside a form
    const aiInput = document.getElementById("ai-input");
    if (aiInput) {
        aiInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                askAI();
            }
        });
    }
});

function toggleTheme() {
    const html = document.documentElement;
    const btn = document.getElementById("theme-toggle");
    
    if (html.classList.contains("light")) {
        html.classList.remove("light");
        html.classList.add("dark");
        if (btn) btn.innerText = "☀️ Light Mode";
    } else {
        html.classList.remove("dark");
        html.classList.add("light");
        if (btn) btn.innerText = "🌙 Dark Mode";
    }
    fetchChartData();
}

async function fetchKPIs() {
    try {
        const res = await fetch(getEndpoint("kpis"));
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();

        if (data && data.total_customers !== undefined) {
            document.getElementById("kpi-total").innerText = Number(data.total_customers).toLocaleString();
            document.getElementById("kpi-avg-risk").innerText = `${data.avg_risk}%`;
            document.getElementById("kpi-high-risk").innerText = Number(data.high_risk_count).toLocaleString();
            document.getElementById("kpi-high-risk-pct").innerText = `${data.high_risk_pct}% share`;
            document.getElementById("kpi-revenue").innerText = data.revenue_at_risk;
        }
    } catch (err) {
        console.error("Failed to fetch KPIs:", err);
    }
}

async function fetchChartData() {
    try {
        const res = await fetch(getEndpoint("charts/risk-distribution"));
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();

        if (!data || !data.labels || !data.data) return;

        const isDark = document.documentElement.classList.contains("dark");
        const textColor = isDark ? '#94a3b8' : '#525252';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

        const canvas = document.getElementById('riskChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        if (chartInstance) chartInstance.destroy();

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: ['#879883', '#b5a897', '#8c424e'],
                    borderRadius: 4,
                    barThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: textColor } },
                    y: { ticks: { color: textColor }, grid: { color: gridColor } }
                }
            }
        });
    } catch (err) {
        console.error("Failed to fetch chart data:", err);
    }
}

async function fetchTableData() {
    try {
        const res = await fetch(getEndpoint("high-risk-customers"));
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const customers = await res.json();

        const tbody = document.getElementById("customer-table-body");
        if (!tbody) return;
        tbody.innerHTML = "";

        if (Array.isArray(customers)) {
            customers.forEach((c, idx) => {
                const row = document.createElement("tr");
                const idCol = c.customer_id || c.customerid || `CUST-${idx + 1001}`;
                const score = (c.risk_score * 100).toFixed(1);

                row.innerHTML = `
                    <td class="py-3.5 px-4 font-mono text-slate-700 dark:text-slate-300">${idCol}</td>
                    <td class="py-3.5 px-4"><span class="px-2.5 py-1 bg-rose-50 dark:bg-rose-950/40 text-heritage-burgundy dark:text-rose-300 border border-rose-200 dark:border-rose-900 rounded-full text-xs font-medium">${c.risk_tier}</span></td>
                    <td class="py-3.5 px-4 font-mono font-semibold text-heritage-burgundy dark:text-rose-400">${score}%</td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (err) {
        console.error("Failed to fetch table data:", err);
    }
}

async function askAI(e) {
    if (e) e.preventDefault();
    
    const input = document.getElementById("ai-input");
    if (!input) return;
    
    const prompt = input.value.trim();
    if (!prompt) return;

    const responseBox = document.getElementById("ai-response");
    if (responseBox) {
        responseBox.innerText = "Processing query against analytical database...";
    }

    try {
        const res = await fetch(getEndpoint("ai-query"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });
        
        const data = await res.json();
        if (responseBox && data && data.insight) {
            responseBox.innerHTML = data.insight;
        }
    } catch (err) {
        console.error("Failed to process AI query:", err);
        if (responseBox) {
            responseBox.innerText = "Unable to process query at this time.";
        }
    }
}

function sendQuickPrompt(text) {
    const input = document.getElementById("ai-input");
    if (input) {
        input.value = text;
        askAI();
    }
}

async function triggerWorkflow() {
    try {
        const res = await fetch(getEndpoint("trigger-workflow"), { method: "POST" });
        const data = await res.json();

        const statusMsg = document.getElementById("workflow-status");
        if (statusMsg && data && data.message) {
            statusMsg.innerText = data.message;
            statusMsg.classList.remove("hidden");
        }
    } catch (err) {
        console.error("Failed to trigger workflow:", err);
    }
}