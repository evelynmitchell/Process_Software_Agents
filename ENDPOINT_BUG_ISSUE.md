# Issue: Persona Endpoints Returning 404

## Status
Critical - All persona endpoints (`/developer`, `/manager`, `/product`) return 404

## Root Causes

### 1. Missing Function Import
**File**: `src/asp/web/developer.py` (lines 149, 164)
- Calls `get_recent_agent_activity(limit=100)` and `get_recent_agent_activity(limit=8)`
- This function does NOT exist in `src/asp/web/data.py`
- Available function: `get_recent_activity()` (different name)
- **Fix**: Replace calls to `get_recent_agent_activity()` with `get_recent_activity()`

### 2. FastHTML Route Registration Error
**Files**: `src/asp/web/developer.py`, `src/asp/web/manager.py`, `src/asp/web/product.py`
- Route functions use `@rt()` decorator **inside** the route registration functions
- These decorators are applied to a bare `rt` that was imported/created at module level
- Should use the `rt` parameter passed into the route registration function
- **Example of incorrect pattern**:
```python
def developer_routes(app, rt):
    @rt('/developer')  # ← This rt is wrong!
    def get_developer():
        ...
```

## Verification
From container logs:
```
INFO:     192.168.1.175:48848 - "GET /developer HTTP/1.1" 404 Not Found
INFO:     192.168.1.175:46392 - "GET /manager HTTP/1.1" 404 Not Found
INFO:     192.168.1.175:40222 - "GET /product HTTP/1.1" 404 Not Found
```

Home route works (`GET / HTTP/1.1` 200 OK), confirming the app initializes but persona routes aren't registered.

## Impact
- Users cannot access any persona dashboards
- Only home page (persona selector) is accessible
- Health check endpoint works (defined in main.py, not persona module)

## Expected Behavior After Fix
- GET `/developer` → Developer dashboard (Alex persona)
- GET `/manager` → Manager dashboard (Sarah persona)  
- GET `/product` → Product dashboard (Jordan persona)
- All HTMX endpoints under each persona route should work
