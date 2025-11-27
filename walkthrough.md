# Walkthrough: Fixing Asyncio Subprocess Error on Windows

## The Issue

You encountered the following error when running the quiz solver:

```
Task exception was never retrieved
...
File "...asyncio\base_events.py", line 539, in _make_subprocess_transport
    raise NotImplementedError
```

### Cause
This error occurs because **Playwright** (used for browser automation) requires `asyncio` to use the **ProactorEventLoop** on Windows to support subprocesses (which browsers are).

However, in some environments or configurations (like when using `uvicorn` with `reload`), Python might default to or be forced into using the **SelectorEventLoop**, which does **not** support subprocesses on Windows, leading to the `NotImplementedError`.

## The Fix

We enforced the usage of `WindowsProactorEventLoopPolicy` at the very beginning of `app.py`, before any event loop is created.

### Changes Made

1.  **Modified `app.py`**:
    Added the following code at the top of the file:
    ```python
    import sys
    import asyncio

    # Fix for Windows + Playwright: Enforce ProactorEventLoopPolicy
    # This must be done before any asyncio loop is created
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    ```

2.  **Cleaned up `quiz_solver.py`**:
    Removed the redundant and ineffective policy setting in `QuizSolver.__init__`. Setting the policy inside a class `__init__` is too late because the event loop is usually already running by then.

## Verification

To verify the fix:

1.  **Restart the Server**:
    If your server is running, stop it (Ctrl+C) and start it again to ensure the new policy takes effect from the start.
    ```bash
    uvicorn app:app --reload
    ```

2.  **Trigger the Quiz Solver**:
    Send a valid request to the `/quiz` endpoint. You can use `test_endpoint.py` or `curl`.
    
    If the fix works, you should no longer see the `NotImplementedError` in the server logs, and the browser should launch (even if headless) and start solving the quiz.

    You should see logs like:
    ```
    INFO:     Starting quiz chain from ...
    INFO:     Loading quiz page: ...
    INFO:     Quiz page loaded...
    ```

    Instead of the crash.
