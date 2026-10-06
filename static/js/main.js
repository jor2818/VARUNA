let currentPeriod = 'all';
let currentDb = 'mb';

document.addEventListener('DOMContentLoaded', () => {
    fetchSummaryData();
});

function setDatabase(db) {
    currentDb = db;

    // Update active database pill states
    const btnMb = document.getElementById('btn-db-mb');
    const btnUtc = document.getElementById('btn-db-utc');

    if (btnMb && btnUtc) {
        if (db === 'mb') {
            btnMb.className = 'pill-btn active';
            btnUtc.className = 'pill-btn';
        } else {
            btnUtc.className = 'pill-btn active';
            btnMb.className = 'pill-btn';
        }
    }

    updateDashboardLinks();
    fetchSummaryData();
}

function updateDashboardLinks() {
    const streamlitUrl = `http://localhost:8501/?db=${encodeURIComponent(currentDb)}`;
    
    ['nav-dashboard-link', 'btn-launch-dashboard', 'btn-hero-dashboard', 'btn-cta-dashboard'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.href = streamlitUrl;
    });
}

function setPeriodFilter(period) {
    currentPeriod = period;
    
    // Update active period pill states
    ['all', 'WD', 'WE'].forEach(p => {
        const btn = document.getElementById(`btn-period-${p.toLowerCase()}`);
        if (btn) {
            if (p.toLowerCase() === period.toLowerCase()) {
                btn.className = 'pill-btn active';
            } else {
                btn.className = 'pill-btn';
            }
        }
    });

    fetchSummaryData();
}

async function fetchSummaryData() {
    const loadingState = document.getElementById('loading-state');
    const summaryContent = document.getElementById('summary-content');
    const errorMessage = document.getElementById('error-message');

    try {
        const url = `/api/summary?db=${encodeURIComponent(currentDb)}&period=${encodeURIComponent(currentPeriod)}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        if (result.status !== 'success') {
            throw new Error(result.message || 'Failed to load summary data');
        }

        const data = result.data;

        // Update Headers & Titles
        const sectionTitle = document.getElementById('section-db-name');
        if (sectionTitle) sectionTitle.textContent = `${data.db_name}`;

        const sectionDesc = document.getElementById('section-db-desc');
        if (sectionDesc) sectionDesc.textContent = `${data.db_description} (${data.active_period} filter)`;

        const statusText = document.getElementById('db-connected-status');
        if (statusText) statusText.textContent = `Connected: ${data.db_name}`;

        // Update Hero Mockup Card
        const mockupCount = document.getElementById('mockup-count-display');
        if (mockupCount) mockupCount.textContent = formatNumber(data.total_vehicles);

        const mockupTopClass = document.getElementById('mockup-top-class');
        if (mockupTopClass) mockupTopClass.textContent = cleanLabel(data.top_vehicle_type);

        const mockupStations = document.getElementById('mockup-stations-count');
        if (mockupStations) mockupStations.textContent = formatNumber(data.total_stations);

        const mockupImports = document.getElementById('mockup-imports-count');
        if (mockupImports) mockupImports.textContent = formatNumber(data.total_imports);

        // Update Key Metrics Cards
        document.getElementById('metric-vehicles').textContent = formatNumber(data.total_vehicles);
        document.getElementById('metric-stations').textContent = formatNumber(data.total_stations);
        document.getElementById('metric-records').textContent = formatNumber(data.total_records);
        document.getElementById('metric-imports').textContent = formatNumber(data.total_imports);
        document.getElementById('metric-latest-import').textContent = formatDate(data.latest_import);
        document.getElementById('metric-top-vehicle').textContent = cleanLabel(data.top_vehicle_type);

        // Update Vehicle Types Progress List
        renderVehicleBreakdown(data.by_vehicle_type);

        // Update Top Stations Table
        renderTopStations(data.top_stations);

        // Hide loading and show content
        if (loadingState) loadingState.classList.add('d-none');
        if (summaryContent) summaryContent.classList.remove('d-none');

        updateDashboardLinks();

    } catch (err) {
        console.error('Error fetching summary stats:', err);
        if (loadingState) loadingState.classList.add('d-none');
        if (errorMessage) {
            errorMessage.textContent = `Error loading metrics: ${err.message}`;
            errorMessage.classList.remove('d-none');
        }
    }
}

function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return Number(num).toLocaleString('en-US');
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
    return dateStr;
}

function cleanLabel(str) {
    if (!str) return 'N/A';
    return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function renderVehicleBreakdown(vehicleList) {
    const container = document.getElementById('vehicle-breakdown-list');
    if (!container) return;

    container.innerHTML = '';
    
    const topVehicles = vehicleList.slice(0, 6);
    
    topVehicles.forEach(item => {
        const row = document.createElement('div');
        row.className = 'mb-3';
        row.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-medium text-dark text-capitalize small">${cleanLabel(item.vehicle_type)}</span>
                <span class="small text-muted">${formatNumber(item.count)} (${item.percentage}%)</span>
            </div>
            <div class="progress">
                <div class="progress-bar" role="progressbar" style="width: ${Math.max(item.percentage, 2)}%" aria-valuenow="${item.percentage}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
        container.appendChild(row);
    });
}

function renderTopStations(stationsList) {
    const container = document.getElementById('top-stations-list');
    if (!container) return;

    container.innerHTML = '';

    if (!stationsList || stationsList.length === 0) {
        container.innerHTML = '<tr><td colspan="3" class="text-muted small">No station data available.</td></tr>';
        return;
    }

    stationsList.forEach(st => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="fw-semibold text-dark">${st.station_code}</td>
            <td><span class="badge-pill">${st.import_count} files</span></td>
            <td class="text-end fw-semibold text-dark">${formatNumber(st.total_traffic)}</td>
        `;
        container.appendChild(tr);
    });
}
