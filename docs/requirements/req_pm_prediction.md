# Requirements: Prediction Engine (Product Manager)

## 1. Overview
A probabilistic estimation and planning tool that uses historical data (PROBE-AI) to predict feature delivery timelines.

## 2. Data Models (TypeScript Interface)

```typescript
// The Feature Request
interface Feature {
  id: string;
  title: string;
  requirements: string[]; // List of specific needs
  uncertainty_score: number; // 0.0 to 1.0 (Higher = Vague)
  status: 'DRAFTING' | 'ESTIMATING' | 'COMMITTED';
}

// The Estimate
interface ProbeEstimate {
  feature_id: string;
  expected_effort_hours: number; // Mean
  confidence_interval_90: [number, number]; // [min, max]
  risk_factors: string[]; // ["New Tech Stack", "Legacy Code Touchpoint"]
  predicted_cost_usd: number;
}

// The Plan
interface TimelineProjection {
  target_date: string; // ISO Date
  probability_of_success: number; // 0.0 to 1.0 (e.g., 0.85 = 85%)
  critical_path: string[]; // List of Feature IDs
}
```

## 3. Input / Output

### Input (Conversation)
*   **Chat Interface:** Natural language description of features.
*   **Clarification Loop:** User answers "Yes/No/Maybe" to agent questions.
*   **Slider Controls:** "Risk Tolerance" vs "Budget" trade-offs.

### Output (Visuals)
*   **Probability Clouds:** Timeline bars with fuzzy edges showing confidence intervals.
*   **Risk Meter:** A gauge showing current requirement ambiguity.
*   **Scenario Simulation:** "What if we cut Feature B?" -> Timeline updates instantly.

## 4. HTML/CSS Mockup

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Prediction Engine - Product Manager</title>
<style>
  :root {
    --bg-app: #ffffff;
    --text-main: #374151;
    --accent-blue: #3b82f6;
    --accent-purple: #8b5cf6;
    --risk-low: #10b981;
    --risk-high: #f59e0b;
  }

  body {
    background-color: var(--bg-app);
    color: var(--text-main);
    font-family: 'Nunito', sans-serif;
    padding: 40px;
    max-width: 1000px;
    margin: 0 auto;
  }

  .container {
    display: flex;
    gap: 40px;
  }

  .chat-panel {
    flex: 1;
    background: #f9fafb;
    border-radius: 12px;
    padding: 20px;
  }

  .viz-panel {
    flex: 2;
  }

  .chat-bubble {
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 12px;
    max-width: 80%;
    font-size: 0.9rem;
  }

  .bubble-agent { background: white; border: 1px solid #e5e7eb; border-top-left-radius: 2px; }
  .bubble-user { background: var(--accent-blue); color: white; margin-left: auto; border-top-right-radius: 2px; }

  .timeline-track {
    position: relative;
    height: 60px;
    background: #f3f4f6;
    border-radius: 8px;
    margin-top: 20px;
    overflow: hidden;
  }

  .timeline-bar {
    position: absolute;
    height: 40px;
    top: 10px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    padding-left: 15px;
    color: white;
    font-weight: bold;
    font-size: 0.8rem;

    /* The "Fuzzy Edge" Effect for Uncertainty */
    background: linear-gradient(90deg,
      rgba(139, 92, 246, 0) 0%,
      rgba(139, 92, 246, 1) 15%,
      rgba(139, 92, 246, 1) 85%,
      rgba(139, 92, 246, 0) 100%
    );
  }

  .stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 15px;
    display: inline-block;
    margin-right: 15px;
    min-width: 120px;
  }

  .stat-val { font-size: 1.5rem; font-weight: bold; color: var(--text-main); }
  .stat-label { font-size: 0.8rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
</head>
<body>

  <h1>New Feature: "Social Login"</h1>

  <div class="container">

    <!-- Chat / Input -->
    <div class="chat-panel">
      <div class="chat-bubble bubble-user">I want users to log in with Google.</div>
      <div class="chat-bubble bubble-agent">Analyzing... I have 2 questions to refine the estimate:</div>
      <div class="chat-bubble bubble-agent">1. Do we need to support mobile native login?</div>
      <div class="chat-bubble bubble-user">No, web only for now.</div>
      <div class="chat-bubble bubble-agent">Updated estimate generated.</div>
    </div>

    <!-- Visualization -->
    <div class="viz-panel">

      <div>
        <div class="stat-card">
          <div class="stat-val">4.5h</div>
          <div class="stat-label">Est. Time</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" style="color:var(--risk-low)">92%</div>
          <div class="stat-label">Confidence</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">$14</div>
          <div class="stat-label">Est. Cost</div>
        </div>
      </div>

      <h3 style="margin-top:30px;">Timeline Projection</h3>

      <!-- Timeline Viz -->
      <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#9ca3af; margin-bottom:5px;">
        <span>Today</span>
        <span>+2 Days</span>
        <span>+1 Week</span>
      </div>

      <div class="timeline-track">
        <!-- The fuzzy bar representing the feature delivery window -->
        <div class="timeline-bar" style="left: 10%; width: 60%;">
          Social Login v1
        </div>
      </div>
      <p style="font-size:0.8rem; color:#6b7280; margin-top:5px;">
        * Faded edges indicate 90% confidence interval range.
      </p>

    </div>

  </div>

</body>
</html>
```
