# Requirements: ASP Overwatch (Engineering Manager)

## 1. Overview
A real-time dashboard for monitoring the health, cost, and quality of autonomous agent squads.

## 2. Data Models (TypeScript Interface)

```typescript
// Core Entity
interface Squad {
  id: string;
  name: string;
  status: 'IDLE' | 'BUSY' | 'ALERT';
  active_agents_count: number;
  current_phase: 'PLANNING' | 'DESIGN' | 'CODE' | 'TEST' | 'REVIEW';
  cost_per_hour: number; // USD
  active_ticket_id?: string;
}

// Telemetry
interface GlobalHealth {
  uptime_percent: number;
  critical_alerts: number;
  monthly_budget_usd: number;
  current_spend_usd: number;
  quality_index: number; // 0.0 to 1.0
  phase_yield_percent: number;
}

// Alert System
interface Anomaly {
  id: string;
  type: 'HIGH_COST' | 'QUALITY_DROP' | 'PROCESS_VIOLATION';
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
  timestamp: string; // ISO 8601
  squad_id?: string;
}
```

## 3. Input / Output

### Input (API Calls)
*   `GET /api/health/global` - Fetches global metrics.
*   `GET /api/squads` - List of all squads and their statuses.
*   `POST /api/config/budget` - Updates budget caps.
*   `POST /api/alerts/{id}/ack` - Acknowledge an anomaly.

### Output (Visuals)
*   **Traffic Light Cards:** Green/Yellow/Red borders based on `Squad.status`.
*   **Sparklines:** Historical trend for `current_spend_usd`.
*   **Notifications:** Toaster popup for new `Anomaly` events.

## 4. HTML/CSS Mockup

```html
<!DOCTYPE html>
<html>
<head>
<style>
  :root {
    --bg-color: #0f172a;
    --card-bg: #1e293b;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --accent-success: #10b981;
    --accent-alert: #ef4444;
  }

  body {
    background-color: var(--bg-color);
    color: var(--text-primary);
    font-family: 'Inter', sans-serif;
    margin: 0;
    padding: 20px;
  }

  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-top: 20px;
  }

  .metric-card {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  .squad-card {
    background-color: var(--card-bg);
    border: 1px solid var(--card-bg);
    border-radius: 8px;
    padding: 16px;
    transition: transform 0.2s;
  }

  .squad-card:hover { transform: translateY(-2px); }

  .squad-card.status-alert { border-color: var(--accent-alert); box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); }
  .squad-card.status-busy { border-color: var(--accent-success); }

  .status-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: bold;
    text-transform: uppercase;
  }

  .badge-alert { background-color: rgba(239, 68, 68, 0.2); color: var(--accent-alert); }
  .badge-busy { background-color: rgba(16, 185, 129, 0.2); color: var(--accent-success); }

  .header { display: flex; justify-content: space-between; align-items: center; }
  h1 { font-size: 1.5rem; margin: 0; }

  .value-large { font-size: 2rem; font-weight: bold; margin: 10px 0; }
  .label-small { color: var(--text-secondary); font-size: 0.875rem; }
</style>
</head>
<body>

  <div class="header">
    <h1>ASP OVERWATCH</h1>
    <div>Sarah (Director)</div>
  </div>

  <!-- Top Metrics -->
  <div class="dashboard-grid">
    <div class="metric-card">
      <div class="label-small">GLOBAL HEALTH</div>
      <div class="value-large" style="color: var(--accent-success)">98%</div>
      <div class="label-small">Uptime (Last 24h)</div>
    </div>
    <div class="metric-card">
      <div class="label-small">BUDGET (MONTH)</div>
      <div class="value-large">$1,240</div>
      <div class="label-small">of $2,000 Cap</div>
    </div>
    <div class="metric-card">
      <div class="label-small">QUALITY INDEX</div>
      <div class="value-large">A-</div>
      <div class="label-small">Phase Yield: 87%</div>
    </div>
  </div>

  <!-- Active Squads -->
  <h2 style="margin-top: 40px; font-size: 1.25rem;">ACTIVE SQUADS</h2>
  <div class="dashboard-grid">

    <!-- Squad 1 -->
    <div class="squad-card status-busy">
      <div style="display:flex; justify-content:space-between;">
        <strong>Checkout Squad</strong>
        <span class="status-badge badge-busy">BUSY</span>
      </div>
      <p class="label-small">Phase: CODE GEN</p>
      <p>Agents Active: 4</p>
      <p class="label-small">Cost: $12.50/hr</p>
      <div style="background:#334155; height:4px; border-radius:2px; margin-top:10px;">
        <div style="background:var(--accent-success); width:60%; height:100%; border-radius:2px;"></div>
      </div>
    </div>

    <!-- Squad 2 -->
    <div class="squad-card status-alert">
      <div style="display:flex; justify-content:space-between;">
        <strong>Auth Squad</strong>
        <span class="status-badge badge-alert">ALERT</span>
      </div>
      <p class="label-small">Phase: BLOCKED</p>
      <p>Agents Active: 0</p>
      <p class="label-small" style="color:var(--accent-alert)">🔴 Sec Review Fail</p>
      <div style="background:#334155; height:4px; border-radius:2px; margin-top:10px;">
        <div style="background:var(--accent-alert); width:90%; height:100%; border-radius:2px;"></div>
      </div>
    </div>

  </div>

</body>
</html>
```
