# UI Design Concept: Flow State Canvas (Developer)

**Persona:** Alex, Senior Developer
**Core Need:** "Focus." (Reduce boilerplate, seamless interaction, intelligent assistance)
**Design Philosophy:** "Infinite Canvas." Not a text editor, but a workspace where code, specs, and chat live together.

---

## 1. The Canvas ("The Workbench")

Alex doesn't work in files; he works in *features*. The UI reflects this.

### Wireframe Layout

```text
+-----------------------------------------------------------------------+
|  [Project: Auth-Service]   [Context: 5 files]   [Agent Status: Idle]  |
+-----------------------------------------------------------------------+
|  TOOLBAR:  [T] Text  [<>] Code  [?] Agent  [#] Plan  [!] Test         |
+-----------------------------------------------------------------------+
|                                                                       |
|           ( Infinite Pan/Zoom Canvas Surface )                        |
|                                                                       |
|   +---------------------+        +-----------------------------+      |
|   | CARD: User Story    |=======>| CARD: Design Spec           |      |
|   | "As a user, I want  |        | - POST /login               |      |
|   | 2FA via SMS..."     |        | - Redis for rate limit      |      |
|   +---------------------+        | - Twilio API                |      |
|             |                    +-----------------------------+      |
|             |                                   |                     |
|             v                                   v                     |
|   +---------------------+        +-----------------------------+      |
|   | AGENT: Planning     |        | CODE BLOCK (generated)      |      |
|   | "I have questions   |        | def send_otp(phone):        |      |
|   | about provider..."  |        |    # ... implementation     |      |
|   | [Reply Here]        |        |                             |      |
|   +---------------------+        +-----------------------------+      |
|                                                 |                     |
|                                                 v                     |
|                                  +-----------------------------+      |
|                                  | TEST RESULTS (Live)         |      |
|                                  | [x] Valid Phone             |      |
|                                  | [ ] Invalid (FAIL)          |      |
|                                  +-----------------------------+      |
|                                                                       |
+-----------------------------------------------------------------------+
|  MINIMAP (Bottom Right)  |  ZOOM: 100%                            |
+-----------------------------------------------------------------------+
```

### Key UI Features

*   **Spatial Organization:** Items are cards connected by lines (dependency arrows). Alex can see that the *Code* depends on the *Design*.
*   **Live Blocks:** The "Code Block" isn't static text. It's a fully functional editor (Monaco based).
*   **Agent Presence:** Agents appear as "cursors" or "avatars" on the canvas. When the Design Agent is writing, Alex sees a ghost cursor typing in the Design card.
*   **"Ghost Comments":** The Review Agent leaves comments *on the edges* connecting cards. (e.g., "This design spec doesn't match the user story requirements" on the arrow between them).

---

## 2. The Interaction Mode ("The Pair Programmer")

When Alex selects a card, the sidebar becomes the "Focus Context".

### Wireframe Layout

```text
+-----------------------------------------------------------------------+
|  CANVAS (Blurred Background)                                          |
|                                                                       |
|  +---------------------------------------------------------------+    |
|  |  FOCUSED CARD: implementation.py                              |    |
|  +---------------------------------------------------------------+    |
|  |                                                               |    |
|  |  [User]                                                       |    |
|  |  "Refactor this to use a strategy pattern for SMS providers." |    |
|  |                                                               |    |
|  |  [Code Agent]                                                 |    |
|  |  "Sure. I'll create an abstract base class `SMSProvider`..."  |    |
|  |                                                               |    |
|  |  [ Diff View ]                                                |    |
|  |  - def send_sms(provider, ...):                               |    |
|  |  + class TwilioProvider(SMSProvider):                         |    |
|  |                                                               |    |
|  |  [Accept]  [Reject]  [Edit]                                   |    |
|  +---------------------------------------------------------------+    |
|                                                                       |
+-----------------------------------------------------------------------+
```

### Key UI Features

*   **Diff-First Interface:** Every agent proposal is shown as a diff. Alex never has to copy-paste.
*   **Quick Actions:** `CMD+K` brings up the Agent Command Palette ("Generate Tests", "Explain Logic", "Find Security Flaws").

---

## 3. The Traceability View ("The History")

Clicking on a line between cards shows the "Why".

*   **Visual:** A timeline of how the requirement evolved into code.
*   **Content:** "Plan v1 -> Design v1 -> Review (Fail) -> Design v2 -> Code v1".

---

## Design Aesthetic
*   **Font:** JetBrains Mono for code, Inter for UI.
*   **Colors:** Soft Gray/Graphite background (Not pure black). Cards are white/light gray with soft shadows.
*   **Vibe:** Creative tool (like Figma or Miro) mixed with an IDE. Playful but precise.
*   **Micro-interactions:** Snappy connecting lines. Cards "pop" when created.
