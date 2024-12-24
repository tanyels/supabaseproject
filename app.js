// Constants
const SUPABASE_URL = 'https://joeyaqjjtnhoapgacazd.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZXlhcWpqdG5ob2FwZ2FjYXpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUwNjAxMzMsImV4cCI6MjA1MDYzNjEzM30.NGf0s9yYGlG-qK-eVVv0HL4sak0UrMO26Kjs3YxnC4o';

// BIST30 Stock List (only stocks with data in Supabase)
const BIST30_STOCKS = [
    'akbnk', 'arclk', 'asels', 'bimas', 'ekgyo', 'eregl', 'froto', 
    'garan', 'kchol', 'kozaa', 'kozal', 'krdmd', 'petkm', 'pgsus', 
    'sahol', 'sasa', 'sise', 'tavhl', 'tcell', 'thyao', 'toaso', 
    'tuprs', 'vakbn', 'ykbnk'
];

// Date range for available stock data
const DATA_RANGE = {
    start: '2019-12-24',
    end: '2024-12-24'
};

// Cache objects
const dataCache = {
    stocks: new Map(),
    exchangeRates: null,
    currentStock: null
};

// Chart state
let currentChartType = 'candlestick';
let currentData = null;

// Initialize variables for chart state
let showLine = true;
let showCandlestick = false;
let showVolume = false;

// Initialize chart
const chartContainer = document.getElementById('chartContainer');
const chart = LightweightCharts.createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: chartContainer.clientHeight,
    layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
    },
    grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
    },
    rightPriceScale: {
        borderColor: '#dfdfdf',
        autoScale: true,
        scaleMargins: {
            top: 0.1,
            bottom: 0.2,
        },
    },
    timeScale: {
        borderColor: '#dfdfdf',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 12,
        barSpacing: 3,
        fixLeftEdge: true,
        lockVisibleTimeRangeOnResize: true,
        rightBarStaysOnScroll: true,
        visible: true,
        minBarSpacing: 0.5,
    },
});

// Create series containers
let candlestickSeries = null;
let lineSeries = null;
let volumeSeries = null;

// Loading overlay control
function showLoading(show = true, message = 'Loading historical data...') {
    const overlay = document.querySelector('.loading-overlay');
    const text = document.querySelector('.loading-text');
    text.textContent = message;
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Initialize chart series
function initializeSeries() {
    // Remove existing series if they exist
    if (candlestickSeries) {
        try {
            chart.removeSeries(candlestickSeries);
            candlestickSeries = null;
        } catch (e) {
            console.log('No candlestick series to remove');
        }
    }
    if (lineSeries) {
        try {
            chart.removeSeries(lineSeries);
            lineSeries = null;
        } catch (e) {
            console.log('No line series to remove');
        }
    }
    if (volumeSeries) {
        try {
            chart.removeSeries(volumeSeries);
            volumeSeries = null;
        } catch (e) {
            console.log('No volume series to remove');
        }
    }
    
    // Create volume series if enabled
    if (showVolume) {
        volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });
    }
    
    // Create line series if enabled
    if (showLine) {
        lineSeries = chart.addLineSeries({
            color: '#2196F3',
            lineWidth: 2,
        });
    }
    
    // Create candlestick series if enabled
    if (showCandlestick) {
        candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
    }
    
    // If we have current data, update the chart
    if (currentData && currentData.length > 0) {
        updateChart(currentData);
    }
}

// Initialize chart type buttons
const lineBtn = document.getElementById('lineBtn');
const candlestickBtn = document.getElementById('candlestickBtn');
const volumeBtn = document.getElementById('volumeBtn');

lineBtn.addEventListener('click', () => toggleChartType('line'));
candlestickBtn.addEventListener('click', () => toggleChartType('candlestick'));
volumeBtn.addEventListener('click', () => toggleChartType('volume'));

// Update button states to reflect initial state
lineBtn.classList.add('active');
candlestickBtn.classList.remove('active');
volumeBtn.classList.remove('active');

function toggleChartType(type) {
    if (type === 'line') {
        showLine = !showLine;
        lineBtn.classList.toggle('active', showLine);
    } else if (type === 'candlestick') {
        showCandlestick = !showCandlestick;
        candlestickBtn.classList.toggle('active', showCandlestick);
    } else if (type === 'volume') {
        showVolume = !showVolume;
        volumeBtn.classList.toggle('active', showVolume);
    }
    
    // Reinitialize series with new settings
    initializeSeries();
    
    // Reapply data if available
    if (currentData) {
        updateChart(currentData);
    }
}

// Initialize stock selector
function initializeStockSelector() {
    const stockSelector = document.getElementById('stockSelector');
    
    BIST30_STOCKS.forEach(stock => {
        const option = document.createElement('option');
        option.value = stock;
        option.textContent = stock.toUpperCase();
        stockSelector.appendChild(option);
    });
    
    stockSelector.addEventListener('change', handleStockChange);
}

// Handle stock change
async function handleStockChange(event) {
    const stockSymbol = event.target.value;
    if (!stockSymbol) return;
    
    showLoading(true, 'Loading historical data...');
    
    try {
        // Check cache first
        if (!dataCache.exchangeRates) {
            showLoading(true, 'Fetching exchange rates...');
            dataCache.exchangeRates = await fetchExchangeRates();
            console.log(`Loaded exchange rates from ${dataCache.exchangeRates[0].date} to ${dataCache.exchangeRates[dataCache.exchangeRates.length - 1].date}`);
        }
        
        let stockData;
        if (dataCache.stocks.has(stockSymbol)) {
            stockData = dataCache.stocks.get(stockSymbol);
        } else {
            showLoading(true, `Fetching ${stockSymbol.toUpperCase()} historical data...`);
            stockData = await fetchStockData(stockSymbol);
            console.log(`Loaded ${stockData.length} records for ${stockSymbol} from ${stockData[0].date} to ${stockData[stockData.length - 1].date}`);
            dataCache.stocks.set(stockSymbol, stockData);
        }
        
        showLoading(true, 'Processing data...');
        
        // Sort data chronologically
        stockData.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        // Convert prices to USD and update chart
        currentData = convertToUSD(stockData, dataCache.exchangeRates);
        dataCache.currentStock = stockSymbol;
        
        if (currentData.length === 0) {
            const exchangeRates = dataCache.exchangeRates;
            throw new Error(`No valid data points in the exchange rate period (${exchangeRates[0].date} to ${exchangeRates[exchangeRates.length - 1].date})`);
        }
        
        updateChart(currentData);
        updatePriceInfo(currentData[currentData.length - 1], stockSymbol);
        
        // Show data range in console
        console.log(`Displaying data for ${stockSymbol.toUpperCase()} from ${currentData[0].time} to ${currentData[currentData.length - 1].time}`);
    } catch (error) {
        console.error('Error handling stock change:', error);
        const exchangeRates = dataCache.exchangeRates;
        alert(`Error loading data for ${stockSymbol.toUpperCase()}. Note: Data is limited to the USD/TRY exchange rate period (${exchangeRates[0].date} to ${exchangeRates[exchangeRates.length - 1].date}).`);
    } finally {
        showLoading(false);
    }
}

// Fetch stock data
async function fetchStockData(stockSymbol) {
    console.log(`Fetching all historical data for ${stockSymbol}...`);
    
    let allData = [];
    let page = 0;
    const pageSize = 1000;
    
    while (true) {
        const response = await fetch(
            `${SUPABASE_URL}/rest/v1/${stockSymbol}?select=date,open,high,low,close,volume&order=date.asc&offset=${page * pageSize}&limit=${pageSize}`, 
            {
                headers: {
                    'apikey': SUPABASE_ANON_KEY,
                    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`Failed to fetch data for ${stockSymbol}`);
        }
        
        const data = await response.json();
        if (data.length === 0) break;
        
        allData = allData.concat(data);
        console.log(`Fetched ${allData.length} records so far...`);
        
        if (data.length < pageSize) break;
        page++;
    }
    
    console.log(`Fetched ${allData.length} records for ${stockSymbol}`);
    
    // Convert dates to proper format
    return allData.map(item => ({
        ...item,
        date: item.date.split('T')[0] // Remove time part if present
    }));
}

// Fetch exchange rates
async function fetchExchangeRates() {
    console.log('Fetching all USD/TRY exchange rates...');
    
    let allRates = [];
    let page = 0;
    const pageSize = 1000;
    
    while (true) {
        const response = await fetch(
            `${SUPABASE_URL}/rest/v1/usdtry?select=date,close&order=date.asc&offset=${page * pageSize}&limit=${pageSize}`,
            {
                headers: {
                    'apikey': SUPABASE_ANON_KEY,
                    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
                }
            }
        );
        
        if (!response.ok) {
            throw new Error('Failed to fetch exchange rates');
        }
        
        const data = await response.json();
        if (data.length === 0) break;
        
        allRates = allRates.concat(data);
        console.log(`Fetched ${allRates.length} exchange rates so far...`);
        
        if (data.length < pageSize) break;
        page++;
    }
    
    console.log(`Fetched ${allRates.length} exchange rates`);
    
    // Convert dates to proper format
    return allRates.map(item => ({
        ...item,
        date: item.date.split('T')[0] // Remove time part if present
    }));
}

// Convert TRY prices to USD
function convertToUSD(stockData, exchangeRates) {
    // Create a map of exchange rates by date
    const rateMap = new Map();
    let lastValidRate = null;
    
    // First pass: collect all available rates and sort them chronologically
    exchangeRates.sort((a, b) => new Date(a.date) - new Date(b.date));
    exchangeRates.forEach(rate => {
        rateMap.set(rate.date, rate.close);
        lastValidRate = rate.close;
    });

    // Get the earliest and latest dates with exchange rates
    const earliestRateDate = exchangeRates[0].date;
    const latestRateDate = exchangeRates[exchangeRates.length - 1].date;
    
    // Convert stock data using exchange rates
    const convertedData = stockData
        .filter(stock => stock.date >= earliestRateDate && stock.date <= latestRateDate)
        .map(stock => {
            // Get exchange rate for this date, or use the last valid rate
            const rate = rateMap.get(stock.date) || lastValidRate;
            
            if (!rate) {
                console.warn(`No exchange rate found for date ${stock.date}`);
                return null;
            }
            
            // Create the data point
            const dataPoint = {
                time: stock.date,
                open: stock.open / rate,
                high: stock.high / rate,
                low: stock.low / rate,
                close: stock.close / rate,
                value: stock.close / rate, // For line chart
                volume: stock.volume || 0,
                exchangeRate: rate
            };
            
            // Validate the data point
            const isValid = 
                dataPoint.open > 0 && 
                dataPoint.high > 0 && 
                dataPoint.low > 0 && 
                dataPoint.close > 0 && 
                !isNaN(dataPoint.open) && 
                !isNaN(dataPoint.high) && 
                !isNaN(dataPoint.low) && 
                !isNaN(dataPoint.close);
            
            if (!isValid) {
                console.warn('Invalid data point:', { original: stock, converted: dataPoint });
                return null;
            }
            
            return dataPoint;
        })
        .filter(item => item !== null);
    
    console.log(`Converted ${convertedData.length} valid data points from ${convertedData[0]?.time} to ${convertedData[convertedData.length - 1]?.time}`);
    return convertedData;
}

// Update chart with new data
function updateChart(data) {
    if (!data || data.length === 0) {
        console.error('No valid data to display');
        return;
    }
    
    console.log(`Updating chart with ${data.length} data points from ${data[0].time} to ${data[data.length - 1].time}`);
    
    // Update line series if enabled
    if (showLine && lineSeries) {
        const lineData = data.map(item => ({
            time: item.time,
            value: item.close,
        }));
        lineSeries.setData(lineData);
    }
    
    // Update candlestick series if enabled
    if (showCandlestick && candlestickSeries) {
        candlestickSeries.setData(data);
    }
    
    // Update volume data if enabled
    if (showVolume && volumeSeries) {
        const volumeData = data.map(item => ({
            time: item.time,
            value: item.volume,
            color: item.close > item.open ? '#26a69a' : '#ef5350',
        }));
        volumeSeries.setData(volumeData);
    }
    
    // Fit content and ensure proper display
    chart.timeScale().fitContent();
    
    // Log the date range
    const firstDate = new Date(data[0].time);
    const lastDate = new Date(data[data.length - 1].time);
    console.log(`Chart data range: ${firstDate.toLocaleDateString()} to ${lastDate.toLocaleDateString()}`);
}

// Update price information
function updatePriceInfo(latestData, stockSymbol) {
    document.getElementById('currentPriceUSD').textContent = `$${latestData.close.toFixed(4)}`;
    document.getElementById('currentPriceTRY').textContent = `₺${(latestData.close * latestData.exchangeRate).toFixed(2)}`;
    
    const dailyChange = ((latestData.close - latestData.open) / latestData.open * 100).toFixed(2);
    document.getElementById('dailyChange').textContent = `${dailyChange}%`;
    document.getElementById('dailyChange').style.color = dailyChange >= 0 ? '#26a69a' : '#ef5350';
    
    document.getElementById('usdTryRate').textContent = latestData.exchangeRate.toFixed(4);
}

// Handle window resize
window.addEventListener('resize', () => {
    chart.applyOptions({
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight,
    });
});

// Initialize the application
initializeSeries();
initializeStockSelector(); 