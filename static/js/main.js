// Global state
let currentSelectedTicker = null;
let isProcessing = false;

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

// Display tickers in sidebar
function displayTickers(tickers) {
    const tickersList = document.getElementById('tickersList');
    
    if (tickers.length === 0) {
        tickersList.innerHTML = `
            <p class="text-gray-500 text-sm text-center py-8">
                <i class="fas fa-info-circle"></i>
                No tickers added yet
            </p>
        `;
        return;
    }
    
    tickersList.innerHTML = tickers.map(ticker => `
        <div class="ticker-item flex items-center justify-between p-3 rounded-lg cursor-pointer transition ${currentSelectedTicker === ticker ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800 hover:bg-gray-200'}"
             onclick="selectTicker('${ticker}')">
            <span class="font-semibold">${ticker}</span>
            <div class="flex gap-2">
                <button onclick="event.stopPropagation(); refreshTicker('${ticker}')" 
                        class="text-xs ${currentSelectedTicker === ticker ? 'text-white hover:text-blue-100' : 'text-blue-600 hover:text-blue-800'}"
                        title="Refresh">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button onclick="event.stopPropagation(); removeTicker('${ticker}')" 
                        class="text-xs ${currentSelectedTicker === ticker ? 'text-white hover:text-red-200' : 'text-red-600 hover:text-red-800'}"
                        title="Remove">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `).join('');
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
    
    try {
        const response = await fetch('/api/tickers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`${symbol} added successfully! Processing...`, 'success');
            input.value = '';
            await loadTickers();
            
            // Select and start processing the new ticker
            setTimeout(() => {
                selectTicker(symbol);
                refreshTicker(symbol);
            }, 500);
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
async function selectTicker(symbol) {
    if (currentSelectedTicker === symbol || isProcessing) {
        return;
    }
    
    currentSelectedTicker = symbol;
    
    // Show loading state
    document.getElementById('welcomeMessage').classList.add('hidden');
    document.getElementById('summaryContainer').classList.add('hidden');
    document.getElementById('loadingState').classList.remove('hidden');
    
    // Update ticker list UI
    const tickers = await fetch('/api/tickers').then(r => r.json()).then(d => d.tickers);
    displayTickers(tickers);
    
    try {
        const response = await fetch(`/api/summary/${symbol}`);
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
            <div class="bg-white rounded-lg shadow-md p-8 text-center">
                <i class="fas fa-info-circle text-4xl text-gray-400 mb-4"></i>
                <p class="text-gray-600 mb-4">No summary available for ${data.symbol} yet.</p>
                <button onclick="refreshTicker('${data.symbol}')" 
                        class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2 mx-auto">
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
        <!-- Latest Summary -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6 fade-in">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <i class="fas fa-file-alt text-blue-600"></i>
                    <span id="currentTicker"></span>
                </h2>
                <span id="summaryDate" class="text-sm text-gray-500"></span>
            </div>
            
            <!-- What Changed Today -->
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                <h3 class="font-bold text-yellow-800 mb-2 flex items-center gap-2">
                    <i class="fas fa-bolt"></i>
                    What Changed Today
                </h3>
                <p id="whatChanged" class="text-gray-700"></p>
            </div>
            
            <!-- Main Summary -->
            <div class="prose max-w-none">
                <h3 class="text-lg font-bold text-gray-800 mb-3">Daily Summary</h3>
                <div id="mainSummary" class="text-gray-700 leading-relaxed"></div>
            </div>
        </div>
        
        <!-- Source Articles -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <i class="fas fa-newspaper"></i>
                Source Articles Used
            </h3>
            <div id="articlesUsed" class="space-y-3"></div>
        </div>
        
        <!-- Historical Summaries -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <i class="fas fa-history"></i>
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
        summaryText.split('\n').filter(p => p.trim()).map(p => `<p class="mb-3">${p}</p>`).join('');
    
    // Display source articles
    const articlesHtml = (data.articles || []).map(article => `
        <div class="article-card border border-gray-200 rounded-lg p-4 hover:border-blue-300">
            <div class="flex items-start gap-3">
                <i class="fas fa-external-link-alt text-blue-600 mt-1"></i>
                <div class="flex-1">
                    <a href="${article.url}" target="_blank" 
                       class="font-semibold text-gray-800 hover:text-blue-600 transition">
                        ${article.title}
                    </a>
                    <p class="text-sm text-gray-500 mt-1">${article.source}</p>
                </div>
            </div>
        </div>
    `).join('');
    document.getElementById('articlesUsed').innerHTML = 
        articlesHtml || '<p class="text-gray-500">No articles available</p>';
    
    // Display historical summaries
    const historicalHtml = (data.historical_summaries || [])
        .slice(1) // Skip the latest (already shown above)
        .map(summary => `
            <div class="border-l-4 border-blue-300 pl-4 py-2">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-semibold text-gray-800">${formatDate(summary.summary_date)}</span>
                </div>
                <p class="text-sm text-gray-600 mb-2">
                    <strong>What Changed:</strong> ${summary.what_changed_today || 'N/A'}
                </p>
                <details class="text-sm text-gray-600">
                    <summary class="cursor-pointer text-blue-600 hover:text-blue-800">
                        View full summary
                    </summary>
                    <div class="mt-2 pl-4 border-l-2 border-gray-200">
                        ${summary.summary_text.substring(0, 300)}...
                    </div>
                </details>
            </div>
        `).join('');
    
    document.getElementById('historicalSummaries').innerHTML = 
        historicalHtml || '<p class="text-gray-500">No historical data available</p>';
    
    document.getElementById('summaryContainer').classList.remove('hidden');
}

// Refresh specific ticker
async function refreshTicker(symbol) {
    if (isProcessing) {
        showNotification('Already processing, please wait...', 'warning');
        return;
    }
    
    isProcessing = true;
    showNotification(`Refreshing ${symbol}...`, 'info');
    
    // Show loading immediately
    if (currentSelectedTicker === symbol) {
        document.getElementById('summaryContainer').classList.add('hidden');
        document.getElementById('welcomeMessage').classList.add('hidden');
        document.getElementById('loadingState').classList.remove('hidden');
    }
    
    try {
        const response = await fetch(`/api/refresh/${symbol}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            
            // Poll for completion - check every 3 seconds
            let attempts = 0;
            const maxAttempts = 25; // 75 seconds max
            
            const checkCompletion = setInterval(async () => {
                attempts++;
                
                try {
                    const summaryResponse = await fetch(`/api/summary/${symbol}`);
                    const summaryData = await summaryResponse.json();
                    
                    if (summaryData.success && summaryData.latest_summary) {
                        clearInterval(checkCompletion);
                        isProcessing = false;
                        
                        if (currentSelectedTicker === symbol) {
                            displaySummary(summaryData);
                        }
                        showNotification(`${symbol} updated successfully!`, 'success');
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkCompletion);
                        isProcessing = false;
                        showNotification('Processing complete. Please click the ticker to view.', 'info');
                        
                        if (currentSelectedTicker === symbol) {
                            document.getElementById('loadingState').classList.add('hidden');
                            selectTicker(symbol);
                        }
                    }
                } catch (error) {
                    console.error('Error checking completion:', error);
                }
            }, 3000);
        } else {
            isProcessing = false;
            showNotification(data.error || 'Refresh failed', 'error');
            document.getElementById('loadingState').classList.add('hidden');
            if (currentSelectedTicker === symbol) {
                selectTicker(symbol);
            }
        }
    } catch (error) {
        isProcessing = false;
        console.error('Error refreshing ticker:', error);
        showNotification('Refresh failed', 'error');
        document.getElementById('loadingState').classList.add('hidden');
        if (currentSelectedTicker === symbol) {
            selectTicker(symbol);
        }
    }
}

// Refresh all tickers
async function refreshAll() {
    if (!confirm('Refresh all tickers? This may take a few minutes.')) return;
    
    showNotification('Refreshing all tickers...', 'info');
    
    try {
        const response = await fetch('/api/refresh-all', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            
            // Reload current ticker after delay
            if (currentSelectedTicker) {
                setTimeout(() => selectTicker(currentSelectedTicker), 20000);
            }
        } else {
            showNotification(data.error || 'Refresh failed', 'error');
        }
    } catch (error) {
        console.error('Error refreshing all:', error);
        showNotification('Refresh failed', 'error');
    }
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

// Notification system
function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in`;
    notification.innerHTML = `
        <div class="flex items-center gap-2">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        notification.style.transition = 'all 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}