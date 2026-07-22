/**
 * GenAI Business Analytics Assistant - Frontend Controller
 */

// Helper: Get active dataset ID
function getActiveDatasetId() {
    return localStorage.getItem('active_dataset_id') || '';
}

function setActiveDatasetId(id) {
    localStorage.setItem('active_dataset_id', id);
}

// 1. Quick Load Sample Datasets
async function loadSampleDataset(sampleKey) {
    try {
        const response = await fetch('/api/datasets/load-sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sample: sampleKey })
        });
        const data = await response.json();
        if (data.success) {
            setActiveDatasetId(data.dataset_id);
            window.location.href = '/dashboard';
        } else {
            alert('Error loading sample dataset: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('Failed to load sample dataset:', err);
        alert('Server communication error.');
    }
}

// 2. Upload Custom File
async function uploadDatasetFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const dropzone = document.getElementById('upload-dropzone');
    if (dropzone) {
        dropzone.innerHTML = `
            <div class="upload-icon"><i class="fas fa-spinner fa-spin"></i></div>
            <h3>Cleaning & Profiling Dataset...</h3>
            <p>Removing duplicates, inferring types, and building SQL database...</p>
        `;
    }
    
    try {
        const response = await fetch('/api/datasets/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            setActiveDatasetId(data.dataset_id);
            window.location.href = '/profiling';
        } else {
            alert('Upload error: ' + (data.error || 'Failed to process dataset'));
            window.location.reload();
        }
    } catch (err) {
        console.error('File upload failed:', err);
        alert('Server communication error during file upload.');
        window.location.reload();
    }
}

// 3. Render Plotly Chart helper
function renderPlotlyChart(elementId, chartSpec) {
    const container = document.getElementById(elementId);
    if (!container || !chartSpec || Object.keys(chartSpec).length === 0) return;
    
    // Ensure responsive layout
    const layout = chartSpec.layout || {};
    layout.autosize = true;
    
    Plotly.newPlot(elementId, chartSpec.data, layout, { responsive: true, displayModeBar: false });
}

// 4. Send AI Chat Question
async function sendChatQuestion() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;
    
    const datasetId = getActiveDatasetId();
    if (!datasetId) {
        alert('Please select or upload a dataset first!');
        window.location.href = '/';
        return;
    }
    
    const messagesContainer = document.getElementById('chat-messages');
    
    // Append User Message
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = query;
    messagesContainer.appendChild(userBubble);
    
    input.value = '';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Loading AI Bubble
    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-bubble ai';
    aiBubble.innerHTML = `<i class="fas fa-robot"></i> Analyzing query & executing SQL... <i class="fas fa-spinner fa-spin"></i>`;
    messagesContainer.appendChild(aiBubble);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await fetch('/api/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: datasetId,
                query: query
            })
        });
        const data = await response.json();
        if (data.success) {
            let contentHtml = `<div>${marked.parse(data.answer_text)}</div>`;
            if (data.sql) {
                contentHtml += `<div class="sql-block"><strong>SQL Executed:</strong><br><code>${data.sql}</code></div>`;
            }
            if (data.chart_spec) {
                const chartId = 'chat-chart-' + Date.now();
                contentHtml += `<div id="${chartId}" style="height:350px; width:100%; margin-top:15px;"></div>`;
                aiBubble.innerHTML = contentHtml;
                setTimeout(() => {
                    renderPlotlyChart(chartId, data.chart_spec);
                }, 100);
            } else {
                aiBubble.innerHTML = contentHtml;
            }
        } else {
            aiBubble.innerHTML = `<span style="color:var(--rose);">Error processing request: ${data.error}</span>`;
        }
    } catch (err) {
        console.error('Chat API failed:', err);
        aiBubble.innerHTML = `<span style="color:var(--rose);">Server communication failure.</span>`;
    }
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 5. PDF Report Generation Trigger
async function downloadPdfReport() {
    const datasetId = getActiveDatasetId();
    if (!datasetId) {
        alert('Please upload or select a dataset first.');
        return;
    }
    
    const btn = document.getElementById('btn-download-pdf');
    if (btn) btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Generating PDF...`;
    
    try {
        const response = await fetch(`/api/reports/generate?dataset_id=${datasetId}`);
        const data = await response.json();
        if (data.success && data.download_url) {
            window.location.href = data.download_url;
        } else {
            alert('PDF Generation failed: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('PDF report failed:', err);
        alert('Failed to generate PDF report.');
    } finally {
        if (btn) btn.innerHTML = `<i class="fas fa-file-pdf"></i> Download PDF Report`;
    }
}

// 6. Forecast Submission Handler
async function runForecast() {
    const datasetId = getActiveDatasetId();
    const metricCol = document.getElementById('forecast-metric-col').value;
    const dateCol = document.getElementById('forecast-date-col').value;
    const periods = document.getElementById('forecast-periods').value;
    
    const container = document.getElementById('forecast-chart-container');
    container.innerHTML = `<div style="text-align:center; padding:3rem;"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Fitting predictive time-series trend model...</p></div>`;
    
    try {
        const response = await fetch('/api/forecast/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: datasetId,
                metric_col: metricCol,
                date_col: dateCol,
                periods: parseInt(periods)
            })
        });
        const data = await response.json();
        if (data.success) {
            container.innerHTML = `<div id="forecast-plotly-plot" style="height:420px; width:100%;"></div>`;
            renderPlotlyChart('forecast-plotly-plot', data.forecast.chart_spec);
            
            // Render forecast table
            const tableBody = document.getElementById('forecast-table-body');
            if (tableBody && data.forecast.forecast_table) {
                tableBody.innerHTML = data.forecast.forecast_table.map(row => `
                    <tr>
                        <td>${row.period}</td>
                        <td style="font-weight:600; color:#34d399;">${row.predicted_value.toLocaleString()}</td>
                        <td style="color:#94a3b8;">${row.lower_bound.toLocaleString()}</td>
                        <td style="color:#94a3b8;">${row.upper_bound.toLocaleString()}</td>
                    </tr>
                `).join('');
            }
        } else {
            container.innerHTML = `<div style="color:var(--rose); padding:2rem;">${data.error}</div>`;
        }
    } catch (err) {
        console.error('Forecast failed:', err);
        container.innerHTML = `<div style="color:var(--rose); padding:2rem;">Failed to run forecast model.</div>`;
    }
}
