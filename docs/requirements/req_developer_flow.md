# Requirements: Flow State Canvas (Developer)

## 1. Overview
An infinite canvas interface for visualizing the software development lifecycle as a directed graph of artifacts and agents.

## 2. Data Models (TypeScript Interface)

```typescript
// The Node on the Canvas
interface CanvasNode {
  id: string;
  type: 'USER_STORY' | 'DESIGN_SPEC' | 'CODE_BLOCK' | 'TEST_RESULT' | 'AGENT_CHAT';
  position: { x: number; y: number };
  content: string | object; // Markdown, JSON, or Code
  status: 'DRAFT' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED';
}

// The Connection
interface Edge {
  id: string;
  source_id: string;
  target_id: string;
  type: 'DEPENDENCY' | 'GENERATED_FROM' | 'RELATES_TO';
  annotations?: string[]; // "Review Agent comments go here"
}

// Real-time Presence
interface AgentCursor {
  agent_id: string; // "planning-agent-01"
  name: string;
  color: string;
  current_node_id: string;
  action: 'WRITING' | 'THINKING' | 'IDLE';
}
```

## 3. Input / Output

### Input (User Actions)
*   `Drag & Drop` - Create connections between nodes.
*   `Double Click` - Edit node content (Monaco Editor).
*   `Context Menu` - "Summon Agent" on a specific node.

### Output (System Responses)
*   **Live Diff:** Agent proposals show as red/green highlighted text within the node.
*   **Ghost Cursors:** Visual indication of where agents are working.
*   **Graph Updates:** Auto-layout adjustments when new nodes are generated.

## 4. HTML/CSS Mockup

```html
<!DOCTYPE html>
<html>
<head>
<style>
  :root {
    --bg-canvas: #f3f4f6;
    --node-bg: #ffffff;
    --text-primary: #111827;
    --border-color: #e5e7eb;
    --primary-color: #3b82f6;
  }

  body {
    background-color: var(--bg-canvas);
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace; /* Developer vibe */
    margin: 0;
    overflow: hidden; /* Infinite canvas feel */
    height: 100vh;
  }

  .toolbar {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: white;
    padding: 10px 20px;
    border-radius: 50px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    display: flex;
    gap: 15px;
    z-index: 100;
  }

  .tool-btn {
    border: none;
    background: none;
    cursor: pointer;
    font-weight: bold;
    color: #4b5563;
  }
  .tool-btn:hover { color: var(--primary-color); }

  .canvas-surface {
    position: relative;
    width: 2000px;
    height: 2000px;
    background-image: radial-gradient(#d1d5db 1px, transparent 1px);
    background-size: 20px 20px;
  }

  .node {
    position: absolute;
    width: 300px;
    background: var(--node-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    padding: 0;
    display: flex;
    flex-direction: column;
  }

  .node-header {
    background: #f9fafb;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color);
    font-weight: bold;
    border-radius: 8px 8px 0 0;
    display: flex;
    justify-content: space-between;
  }

  .node-body {
    padding: 12px;
    font-size: 0.85rem;
    line-height: 1.4;
  }

  .edge-line {
    position: absolute;
    height: 2px;
    background: #9ca3af;
    transform-origin: 0 0;
    z-index: -1;
  }

  .agent-cursor {
    position: absolute;
    padding: 4px 8px;
    background: var(--primary-color);
    color: white;
    border-radius: 4px;
    font-size: 0.7rem;
    pointer-events: none;
    transition: all 0.2s;
  }
</style>
</head>
<body>

  <div class="toolbar">
    <button class="tool-btn">[T] Text</button>
    <button class="tool-btn">[<>] Code</button>
    <button class="tool-btn" style="color:var(--primary-color)">[+] Agent</button>
  </div>

  <div class="canvas-surface">

    <!-- Node 1: User Story -->
    <div class="node" style="top: 100px; left: 100px;">
      <div class="node-header">
        <span>STORY-101</span>
        <span>✅</span>
      </div>
      <div class="node-body">
        As a user, I want to reset my password via email magic link.
      </div>
    </div>

    <!-- Connector Line (Simulated) -->
    <div class="edge-line" style="top: 140px; left: 402px; width: 100px; transform: rotate(15deg);"></div>

    <!-- Node 2: Design Spec -->
    <div class="node" style="top: 150px; left: 500px; border: 2px solid var(--primary-color);">
      <div class="node-header">
        <span>DESIGN-SPEC</span>
        <span style="font-size:0.7em; color:gray;">Thinking...</span>
      </div>
      <div class="node-body">
        <span style="color:green;">+ POST /auth/reset-password</span><br>
        <span style="color:green;">+ Generate secure token (JWT)</span><br>
        <span style="color:gray;">// Agent is typing here...</span>
      </div>

      <!-- Agent Cursor Overlay -->
      <div class="agent-cursor" style="bottom: -10px; right: -10px;">
        🤖 Design Agent
      </div>
    </div>

  </div>

</body>
</html>
```
