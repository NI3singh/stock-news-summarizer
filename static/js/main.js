
// Global state
let currentSelectedTicker = null;
let isProcessing = false;

// NEW: which ticker is currently being processed (so UI can show loading for that ticker)
let processingTicker = null;
let processingTickersSet = new Set();
let batchRefreshActive = false;
let userInteractedDuringBatch = false;
let initiallySelectedTicker = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTickers();
});

// Load all tickers
async function loadTickers() {
    try {
        const response = await fetch('/api/tickers');
        const data = await response.json();

        if (data.success && data.tickers.length > 0) {
            displayTickers(data.tickers);
            // Auto-select first ticker only if none selected
            if (!currentSelectedTicker) {
                selectTicker(data.tickers[0]);
            } else if (!data.tickers.includes(currentSelectedTicker)) {
                // If current ticker was deleted, select first one
                currentSelectedTicker = null;
                selectTicker(data.tickers[0]);
            }
        } else {
            document.getElementById('tickersList').innerHTML = `
                <p class="text-gray-500 text-sm text-center py-8">
                    <i class="fas fa-info-circle"></i>
                    Add a ticker to get started
                </p>
            `;
            document.getElementById('welcomeMessage').classList.remove('hidden');
            document.getElementById('summaryContainer').classList.add('hidden');
            currentSelectedTicker = null;
        }
    } catch (error) {
        console.error('Error loading tickers:', error);
        showNotification('Failed to load tickers', 'error');
    }
}


// Display tickers in sidebar (handles multiple processing tickers and marks user clicks)
function displayTickers(tickers) {
    const tickersList = document.getElementById('tickersList');

    if (tickers.length === 0) {
        tickersList.innerHTML = `
            <p class="text-slate-500 text-sm text-center py-6">
                <i class="fas fa-info-circle"></i>
                No tickers added yet
            </p>
        `;
        return;
    }

    tickersList.innerHTML = tickers.map(ticker => {
        // If this ticker is currently being processed, show a small spinner badge
        const isProcessingThis = (processingTicker === ticker) || processingTickersSet.has(ticker);
        const processingBadge = isProcessingThis
            ? `<span class="ml-2 text-xs px-2 py-1 rounded bg-yellow-600 text-white">Processing</span>`
            : '';

        // NOTE: onclick sets userInitiated=true so selectTicker knows user manually selected this ticker
        return `
        <div class="ticker-item flex items-center justify-between p-3 ${currentSelectedTicker === ticker ? 'active text-white' : 'text-slate-300'}"
             onclick="selectTicker('${ticker}', true)">
            <div class="flex items-center gap-2">
                <span class="font-bold">${ticker}</span>
                ${processingBadge}
            </div>
            <div class="flex gap-1">
                <button onclick="event.stopPropagation(); refreshTicker('${ticker}')"
                        class="p-2 rounded-lg transition ${currentSelectedTicker === ticker ? 'hover:bg-white hover:bg-opacity-10' : 'hover:bg-slate-700'}"
                        title="Refresh">
                    <i class="fas fa-sync-alt text-xs"></i>
                </button>
                <button onclick="event.stopPropagation(); removeTicker('${ticker}')"
                        class="p-2 rounded-lg transition ${currentSelectedTicker === ticker ? 'hover:bg-white hover:bg-opacity-10' : 'hover:bg-slate-700'}"
                        title="Remove">
                    <i class="fas fa-times text-xs"></i>
                </button>
            </div>
        </div>
    `;
    }).join('');
}




// Add new ticker
async function addTicker() {
    const input = document.getElementById('newTickerInput');
    const symbol = input.value.trim().toUpperCase();

    if (!symbol) {
        showNotification('Please enter a ticker symbol', 'warning');
        return;
    }

    if (symbol.length > 10) {
        showNotification('Invalid ticker symbol', 'error');
        return;
    }

    if (isProcessing) {
        showNotification('Already processing, please wait...', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/tickers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`${symbol} added successfully! Processing...`, 'success');
            input.value = '';

            // Immediately show loading state
            currentSelectedTicker = symbol;
            document.getElementById('welcomeMessage').classList.add('hidden');
            document.getElementById('summaryContainer').classList.add('hidden');
            document.getElementById('loadingState').classList.remove('hidden');

            // Load tickers to update sidebar
            await loadTickers();

            // Start processing
            refreshTicker(symbol);
        } else {
            showNotification(data.error || 'Failed to add ticker', 'error');
        }
    } catch (error) {
        console.error('Error adding ticker:', error);
        showNotification('Failed to add ticker', 'error');
    }
}

// Handle Enter key in ticker input
function handleTickerKeyPress(event) {
    if (event.key === 'Enter') {
        addTicker();
    }
}

// Remove ticker
async function removeTicker(symbol) {
    if (!confirm(`Remove ${symbol}?`)) return;

    try {
        const response = await fetch(`/api/tickers/${symbol}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`${symbol} removed`, 'success');

            // Clear current selection if it's the removed ticker
            if (currentSelectedTicker === symbol) {
                currentSelectedTicker = null;
            }

            await loadTickers();
        } else {
            showNotification(data.error || 'Failed to remove ticker', 'error');
        }
    } catch (error) {
        console.error('Error removing ticker:', error);
        showNotification('Failed to remove ticker', 'error');
    }
}

// Select and display ticker summary
async function selectTicker(symbol, userInitiated = false) {
    // If this selection is user-initiated while a batch refresh is running, mark it
    if (batchRefreshActive && userInitiated) {
        userInteractedDuringBatch = true;
    }

    // If user clicked the already-selected ticker and not processing, do nothing
    if (currentSelectedTicker === symbol && !isProcessing) {
        return;
    }

    currentSelectedTicker = symbol;

    // Show loading state (we allow selection to fetch the currently available summary)
    document.getElementById('welcomeMessage').classList.add('hidden');
    document.getElementById('summaryContainer').classList.add('hidden');
    document.getElementById('loadingState').classList.remove('hidden');

    // Update ticker list UI
    try {
        const tickers = await fetch('/api/tickers', { cache: 'no-store' }).then(r => r.json()).then(d => d.tickers);
        displayTickers(tickers);
    } catch (e) {
        console.warn('Could not refresh ticker list before showing summary', e);
    }

    try {
        // cache-busted fetch
        const response = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' });
        const data = await response.json();

        if (data.success) {
            displaySummary(data);
        } else {
            showNotification(data.error || 'Failed to load summary', 'error');
            document.getElementById('loadingState').classList.add('hidden');
            document.getElementById('summaryContainer').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading summary:', error);
        showNotification('Failed to load summary', 'error');
        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('welcomeMessage').classList.remove('hidden');
    }
}

// Display summary data
function displaySummary(data) {
    document.getElementById('loadingState').classList.add('hidden');

    if (!data.latest_summary) {
        document.getElementById('summaryContainer').innerHTML = `
            <div class="card p-10 text-center">
                <i class="fas fa-info-circle text-4xl text-slate-600 mb-4"></i>
                <p class="text-slate-400 mb-4">No summary available for ${data.symbol} yet.</p>
                <button onclick="refreshTicker('${data.symbol}')"
                        class="btn-primary text-white px-6 py-2 rounded-lg transition font-medium inline-flex items-center gap-2">
                    <i class="fas fa-sync-alt"></i>
                    <span>Generate Summary</span>
                </button>
            </div>
        `;
        document.getElementById('summaryContainer').classList.remove('hidden');
        return;
    }

    // Restore the full summary container HTML first
    document.getElementById('summaryContainer').innerHTML = `
        <div class="card p-6 fade-in">
            <div class="flex items-center justify-between mb-5">
                <h2 class="text-2xl font-bold text-blue-500" id="currentTicker"></h2>
                <span id="summaryDate" class="text-sm text-slate-400"></span>
            </div>
            
            <div class="what-changed p-4 rounded-lg mb-5">
                <h3 class="font-bold mb-2 flex items-center gap-2">
                    <i class="fas fa-bolt"></i>
                    What Changed Today
                </h3>
                <p id="whatChanged" class="text-sm"></p>
            </div>
            
            <div>
                <h3 class="text-lg font-bold text-white mb-3 flex items-center gap-2">
                    <i class="fas fa-file-alt text-blue-500"></i>
                    Daily Summary
                </h3>
                <div id="mainSummary" class="text-slate-300 leading-relaxed space-y-2"></div>
            </div>
        </div>
        
        <div class="card p-6">
            <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <i class="fas fa-newspaper text-blue-500"></i>
                Source Articles
            </h3>
            <div id="articlesUsed" class="space-y-3"></div>
        </div>
        
        <div class="card p-6">
            <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <i class="fas fa-history text-blue-500"></i>
                7-Day History
            </h3>
            <div id="historicalSummaries" class="space-y-4"></div>
        </div>
    `;

    // Update current ticker display
    document.getElementById('currentTicker').textContent = data.symbol;
    document.getElementById('summaryDate').textContent = formatDate(data.latest_summary.summary_date);

    // Display "What Changed Today"
    document.getElementById('whatChanged').textContent =
        data.latest_summary.what_changed_today || 'No changes noted';

    // Display main summary
    const summaryText = data.latest_summary.summary_text || 'No summary available';
    document.getElementById('mainSummary').innerHTML =
        summaryText.split('\n').filter(p => p.trim()).map(p => `<p class="mb-2">${p}</p>`).join('');

    // Display source articles
    const articlesHtml = (data.articles || []).map(article => `
        <div class="article-card bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div class="flex items-start gap-3">
                <i class="fas fa-external-link-alt text-blue-500 mt-1"></i>
                <div class="flex-1">
                    <a href="${article.url}" target="_blank"
                       class="font-semibold text-slate-200 hover:text-blue-400 transition">
                        ${article.title}
                    </a>
                    <p class="text-xs text-slate-500 mt-1">${article.source}</p>
                </div>
            </div>
        </div>
    `).join('');
    document.getElementById('articlesUsed').innerHTML =
        articlesHtml || '<p class="text-slate-500">No articles available</p>';

    // Display historical summaries
    const historicalHtml = (data.historical_summaries || [])
        .slice(1) // Skip the latest (already shown above)
        .map(summary => `
            <div class="border-l-2 border-blue-500 pl-4 py-2">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-semibold text-white">${formatDate(summary.summary_date)}</span>
                </div>
                <p class="text-sm text-slate-400 mb-2">
                    <strong>What Changed:</strong> ${summary.what_changed_today || 'N/A'}
                </p>
                <details class="text-sm text-slate-400">
                    <summary class="cursor-pointer text-blue-400 hover:text-blue-300">
                        View full summary
                    </summary>
                    <div class="mt-2 pl-3 border-l border-slate-700 text-slate-500">
                        ${summary.summary_text.substring(0, 300)}...
                    </div>
                </details>
            </div>
        `).join('');

    document.getElementById('historicalSummaries').innerHTML =
        historicalHtml || '<p class="text-slate-500">No historical data available</p>';

    document.getElementById('summaryContainer').classList.remove('hidden');
}

async function refreshTicker(symbol) {
    if (isProcessing) {
        showNotification('Already processing, please wait...', 'warning');
        return;
    }

    isProcessing = true;
    processingTicker = symbol;
    processingTickersSet.add(symbol);
    showNotification(`Starting refresh for ${symbol}...`, 'info');

    // Update UI list
    try { const tl = await fetch('/api/tickers', { cache: 'no-store' }).then(r=>r.json()).then(d=>d.tickers); displayTickers(tl); } catch(e){}

    // Request refresh -> expect job_id
    let jobId = null;
    try {
        const resp = await fetch(`/api/refresh/${symbol}`, { method: 'POST' });
        const json = await resp.json();
        if (json && json.success && json.job_id) {
            jobId = json.job_id;
        } else {
            // fallback to summary-polling if job_id not provided
        }
    } catch (e) {
        console.error('refresh POST failed', e);
    }

    const finishSuccess = async (summaryData) => {
        processingTickersSet.delete(symbol);
        isProcessing = false;
        processingTicker = null;
        try { const tl = await fetch('/api/tickers', { cache: 'no-store' }).then(r=>r.json()).then(d=>d.tickers); displayTickers(tl); } catch(e){}
        if (currentSelectedTicker === symbol && summaryData) {
            displaySummary(summaryData);
        }
        showNotification(`${symbol} updated successfully!`, 'success');
    };

    const finishFailure = async (reason) => {
        processingTickersSet.delete(symbol);
        isProcessing = false;
        processingTicker = null;
        try { const tl = await fetch('/api/tickers', { cache: 'no-store' }).then(r=>r.json()).then(d=>d.tickers); displayTickers(tl); } catch(e){}
        showNotification(`Refresh for ${symbol} failed: ${reason}`, 'error');
    };

    if (jobId) {
        // Poll job endpoint until done/failed
        const maxAttempts = 120;
        let attempts = 0;
        const iv = setInterval(async () => {
            attempts++;
            try {
                const res = await fetch(`/api/job/${jobId}`, { cache: 'no-store' });
                const j = await res.json();
                if (j && j.success) {
                    if (j.status === 'done') {
                        clearInterval(iv);
                        // Prefer job result if present
                        const summaryResult = j.result ? { success: true, latest_summary: j.result, articles: [] , symbol } : null;
                        await finishSuccess(summaryResult);
                        return;
                    } else if (j.status === 'failed') {
                        clearInterval(iv);
                        await finishFailure('backend job failed');
                        return;
                    }
                }
            } catch (err) {
                console.error('Job poll error', err);
            }
            if (attempts >= maxAttempts) {
                clearInterval(iv);
                // fallback: final try to fetch summary
                try {
                    const finalResp = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' });
                    const finalJson = await finalResp.json();
                    if (finalJson && finalJson.success && finalJson.latest_summary) {
                        await finishSuccess(finalJson);
                    } else {
                        await finishFailure('timeout');
                    }
                } catch (e) {
                    await finishFailure('timeout');
                }
            }
        }, 2000);
    } else {
        // Fallback: if backend didn't return job_id (older server), do robust summary polling
        const baselineResp = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' });
        const baselineJson = await baselineResp.json();
        const baselineCreated = baselineJson?.latest_summary?.created_at || null;
        const baselineText = (baselineJson?.latest_summary?.summary_text || '').trim() || null;
        const refreshStartTime = Date.now();

        let attempts = 0;
        const maxAttempts = 120;
        const iv = setInterval(async () => {
            attempts++;
            try {
                const sres = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' });
                const sj = await sres.json();
                if (sj && sj.success && sj.latest_summary) {
                    const latest = sj.latest_summary;
                    const latestCreated = latest.created_at || latest.updated_at || null;
                    const latestText = (latest.summary_text || '').trim();
                    let isNew = false;
                    if (baselineCreated && latestCreated && latestCreated !== baselineCreated) isNew = true;
                    if (!isNew && baselineText && latestText && latestText !== baselineText) isNew = true;
                    if (!isNew && !baselineText && latestText && latestText.length > 30) isNew = true;
                    if (isNew) {
                        clearInterval(iv);
                        await finishSuccess(sj);
                        return;
                    }
                }
            } catch (err) {
                console.error('Summary poll error', err);
            }
            if (attempts >= maxAttempts) {
                clearInterval(iv);
                try {
                    const finalResp = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' });
                    const finalJson = await finalResp.json();
                    if (finalJson && finalJson.success && finalJson.latest_summary) {
                        await finishSuccess(finalJson);
                    } else {
                        await finishFailure('timeout');
                    }
                } catch (e) {
                    await finishFailure('timeout');
                }
            }
        }, 2000);
    }
}

async function refreshAll() {
    if (!confirm('Refresh all tickers? This may take a few minutes.')) return;
    if (isProcessing) {
        showNotification('Another refresh is in progress. Please wait...', 'warning');
        return;
    }

    isProcessing = true;
    batchRefreshActive = true;
    userInteractedDuringBatch = false;
    initiallySelectedTicker = currentSelectedTicker;

    showNotification('Refresh all started', 'info');

    // Get tickers
    let tickers = [];
    try {
        const tr = await fetch('/api/tickers', { cache: 'no-store' });
        const j = await tr.json();
        tickers = j.tickers || [];
    } catch (e) {
        console.error('failed to fetch tickers', e);
        isProcessing = false;
        return;
    }
    if (tickers.length === 0) {
        showNotification('No tickers to refresh.', 'info');
        isProcessing = false;
        batchRefreshActive = false;
        return;
    }

    // POST /api/refresh-all -> prefer job_map if returned
    let jobMap = null;
    try {
        const resp = await fetch('/api/refresh-all', { method: 'POST' });
        const json = await resp.json();
        if (json && json.success && json.job_map) {
            jobMap = json.job_map; // { symbol: job_id, ... }
        } else {
            // no job_map — fallback; we'll poll summaries per-ticker
        }
    } catch (e) {
        console.error('refresh-all POST failed', e);
    }

    // Show badges
    tickers.forEach(t => processingTickersSet.add(t));
    try { displayTickers(tickers); } catch (e){}

    // Polling helper that either polls job endpoint or falls back to summary polling
    const pollSingle = (symbol, jobId=null) => {
        if (jobId) {
            return new Promise((resolve) => {
                const maxAttempts = 120;
                let attempts = 0;
                const iv = setInterval(async () => {
                    attempts++;
                    try {
                        const res = await fetch(`/api/job/${jobId}`, { cache: 'no-store' });
                        const j = await res.json();
                        if (j && j.success) {
                            if (j.status === 'done') {
                                clearInterval(iv);
                                resolve({ symbol, success: true, data: { success: true, latest_summary: j.result } });
                                return;
                            } else if (j.status === 'failed') {
                                clearInterval(iv);
                                resolve({ symbol, success: false, reason: 'failed' });
                                return;
                            }
                        }
                    } catch (e) {
                        console.error('job poll error', e);
                    }
                    if (attempts >= maxAttempts) {
                        clearInterval(iv);
                        resolve({ symbol, success: false, reason: 'timeout' });
                        return;
                    }
                }, 2000);
            });
        } else {
            // fallback summary polling
            return new Promise(async (resolve) => {
                let baseline = { createdAt: null, summaryText: null };
                try {
                    const b = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' }).then(r=>r.json());
                    if (b && b.success && b.latest_summary) {
                        baseline.createdAt = b.latest_summary.created_at || null;
                        baseline.summaryText = (b.latest_summary.summary_text || '').trim() || null;
                    }
                } catch (e) {}
                let attempts = 0;
                const maxAttempts = 120;
                const iv = setInterval(async () => {
                    attempts++;
                    try {
                        const s = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' }).then(r=>r.json());
                        if (s && s.success && s.latest_summary) {
                            const latest = s.latest_summary;
                            const latestCreated = latest.created_at || latest.updated_at || null;
                            const latestText = (latest.summary_text || '').trim();
                            let isNew = false;
                            if (baseline.createdAt && latestCreated && latestCreated !== baseline.createdAt) isNew = true;
                            if (!isNew && baseline.summaryText && latestText && latestText !== baseline.summaryText) isNew = true;
                            if (!isNew && !baseline.summaryText && latestText && latestText.length > 30) isNew = true;
                            if (isNew) {
                                clearInterval(iv);
                                resolve({ symbol, success: true, data: s });
                                return;
                            }
                        }
                    } catch (e) { console.error('summary poll fallback error', e); }
                    if (attempts >= maxAttempts) {
                        clearInterval(iv);
                        try {
                            const final = await fetch(`/api/summary/${symbol}?cb=${Date.now()}`, { cache: 'no-store' }).then(r=>r.json());
                            if (final && final.success && final.latest_summary) resolve({ symbol, success: true, data: final });
                            else resolve({ symbol, success: false, reason: 'timeout' });
                        } catch (e) { resolve({ symbol, success: false, reason: 'timeout' }); }
                    }
                }, 2000);
            });
        }
    };

    // Start polling for all tickers and attach per-ticker handlers
    const pollPromises = tickers.map(sym => pollSingle(sym, jobMap ? jobMap[sym] : null));
    let successCount = 0;
    pollPromises.forEach(p => {
        p.then(info => {
            try {
                const sym = info.symbol;
                processingTickersSet.delete(sym);
                (async ()=>{ try { const tnow = await fetch('/api/tickers', { cache: 'no-store' }).then(r => r.json()).then(d => d.tickers); displayTickers(tnow); } catch(e){} })();
                if (info.success) {
                    successCount++;
                    if (!userInteractedDuringBatch && initiallySelectedTicker === sym) {
                        try { displaySummary(info.data); } catch(e) {}
                    } else if (currentSelectedTicker === sym) {
                        try { displaySummary(info.data); } catch(e) {}
                    }
                    showNotification(`${sym} refreshed`, 'success');
                } else {
                    showNotification(`${sym} refresh failed or timed out`, 'warning');
                }
            } catch (e) {
                console.error('per-promise handler error', e);
            }
        }).catch(err => console.error('poll promise error', err));
    });

    // Wait for all to finish
    await Promise.allSettled(pollPromises);
    showNotification(`All tickers processed (${successCount}/${tickers.length} succeeded)`, 'success');

    // Final UI refresh
    try {
        processingTickersSet.clear();
        const finalTickers = await fetch('/api/tickers', { cache: 'no-store' }).then(r => r.json()).then(d => d.tickers);
        displayTickers(finalTickers);
        if (currentSelectedTicker) {
            const finalResp = await fetch(`/api/summary/${currentSelectedTicker}?cb=${Date.now()}`, { cache: 'no-store' });
            const finalJson = await finalResp.json();
            if (finalJson && finalJson.success && finalJson.latest_summary) displaySummary(finalJson);
        }
    } catch (e) {
        console.error('final fetch error', e);
    }

    // Cleanup
    isProcessing = false;
    batchRefreshActive = false;
    userInteractedDuringBatch = false;
    initiallySelectedTicker = null;
}


// Utility: Format date
function formatDate(dateStr) {
    if (!dateStr) return 'Unknown date';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function showNotification(message, type = 'info') {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }

    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;

    // Add to container
    container.appendChild(notif);

    // Smooth entry
    setTimeout(() => notif.classList.add('show'), 10);

    // Remove after 4s with exit animation
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 4000);
}
