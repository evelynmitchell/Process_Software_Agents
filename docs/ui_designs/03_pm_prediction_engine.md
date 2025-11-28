# UI Design Concept: Prediction Engine (Product Manager)

**Persona:** Jordan, Product Manager
**Core Need:** "Certainty." (Estimation, Timeline, Requirements Clarity)
**Design Philosophy:** "The Weather Forecast." Probabilistic, timeline-based, and friendly.

---

## 1. The Feature Wizard ("The Input")

Jordan doesn't write JIRA tickets; they converse with the Planning Agent to build a spec.

### Wireframe Layout

```text
+-----------------------------------------------------------------------+
|  NEW FEATURE: "Social Login"                                          |
+-----------------------------------------------------------------------+
|  REQUIREMENTS INPUT                                                   |
|  "I want users to log in with Google and GitHub."                     |
|                                                                       |
|  [ Analyzed by Planning Agent... ]                                    |
|                                                                       |
|  CLARIFICATION NEEDED (3 Questions):                                  |
|  1. "Should we merge accounts if the email matches?" [Yes/No]         |
|  2. "Do we need to support Enterprise SSO?"          [Later]          |
|  3. "What happens if the provider is down?"          [Show Error]     |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  LIVE ESTIMATE (PROBE-AI)                                       |  |
|  |  Est. Cost: $12.40  |  Est. Time: 4.5 hrs  |  Risk: LOW         |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  [ Create Feature ]                                                   |
+-----------------------------------------------------------------------+
```

### Key UI Features

*   **Conversational Form:** It feels like a chat, but it structures the data into a requirement doc in real-time.
*   **Real-time Ticker:** As Jordan answers questions (reducing ambiguity), the "Risk" meter goes down and the "Est. Time" becomes more precise.
*   **Confidence Intervals:** The estimate isn't "4 hours", it's "3.5 - 5.5 hours (90% confidence)".

---

## 2. The Crystal Ball ("The Timeline")

Not a Gantt chart, but a "Probability Cloud" timeline.

### Wireframe Layout

```text
+-----------------------------------------------------------------------+
|  PROJECT TIMELINE: Q4 Launch                                          |
+-----------------------------------------------------------------------+
|  TODAY  |  WEEK 1      |  WEEK 2      |  WEEK 3      |  WEEK 4        |
+---------+--------------+--------------+--------------+----------------+
|         |              |              |              |                |
|  [ Feature A: Search ]==================> [Launch]   |                |
|         |              |              |              |                |
|         |    [ Feature B: Payments ]========================> [??]    |
|         |              |              |   (Confidence: 40%)           |
|         |              |              |   (Risk: Integration)         |
|         |              |              |              |                |
|         |              |   [ Feature C: Analytics ]======> [Launch]   |
|         |              |              |              |                |
+---------+--------------+--------------+--------------+----------------+
|  SIMULATION RESULTS (Based on velocity)                               |
|  • 80% chance of shipping all features by Nov 15th.                   |
|  • 20% chance of shipping by Nov 1st (Aggressive).                    |
|  • SUGGESTION: Drop "Feature B" to guarantee Nov 1st launch.          |
+-----------------------------------------------------------------------+
```

### Key UI Features

*   **Fuzzy Edges:** Task bars don't have hard edges. They fade out, representing uncertainty.
*   **"What If" Scenarios:** A sidebar allows Jordan to drag a slider ("Team Capacity", "Budget") and watch the timeline reshape instantly.
*   **Dependency Visualization:** Hovering over "Payments" highlights "Search" in red if it's a blocker.

---

## 3. The Velocity Tracker ("The Stock Market")

Tracking the team's "Graduation" status.

*   **Visual:** "Achievement Badges" style.
*   **Content:**
    *   "Test Agent: Level 4 (Autonomous)" - 98% Accuracy.
    *   "Design Agent: Level 2 (Shadow Mode)" - 60% Accuracy.
*   **Meaning:** "As agents level up, your velocity multiplier increases."

---

## Design Aesthetic
*   **Font:** Rounded sans-serif (e.g., Nunito or Quicksand). Friendly and approachable.
*   **Colors:** White background, soft pastels (Mint Green, Sky Blue, Coral).
*   **Vibe:** Modern SaaS (like Linear or Notion). Clean, optimistic, airy.
*   **Visual Metaphors:** Weather icons (Sunny = High Confidence, Cloudy = Uncertainty).
