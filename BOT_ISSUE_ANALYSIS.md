# AIStoryWriter Telegram Bot - Issue Analysis

## Date: 2026-04-09

## Current Status
- Bot is STUCK in infinite retry loop
- Running since: 2026-04-08 11:50:00 (21+ hours)
- Current retry attempt: 1054+
- Process PIDs:
  - TelegramBot.py: 3056641
  - Write.py: 3626588

## Root Cause

### Problem 1: Infinite Retry Loops
File: `Writer/Interface/Wrapper.py`

Two functions have infinite retry loops with NO maximum limit:

1. **SafeGenerateText()** (line 159):
```python
while (self.GetLastMessageText(NewMsg).strip() == "") or (len(self.GetLastMessageText(NewMsg).split(" ")) < _MinWordCount):
    # Retries forever if model returns whitespace
```

2. **SafeGenerateJSON()** (line 181):
```python
while True:
    # Retries forever if JSON parsing fails
```

### Problem 2: Context Length Explosion
- Started with: ~476 tokens
- Current context: ~131,147 tokens (16x over limit!)
- Model limit: 8,192 tokens (llama3)
- Model configured with: `{'num_ctx': 8192}`

When context exceeds model capacity:
- Model returns whitespace or invalid JSON
- Code retries, adding MORE context
- Context grows larger each retry
- Creates infinite loop

## Log Evidence

```
[4 ] [2026-04-09_08-49-21] Using Model 'llama3' from 'ollama@localhost:11434' | (Est. ~131147.0tok Context Length)
[6 ] [2026-04-09_08-49-21] Warning, Detected High Token Context Length of est. ~131147.0tok
[4 ] [2026-04-09_08-49-21] Using Ollama Model Options: {'num_ctx': 8192}
[4 ] [2026-04-09_08-49-21] Generated Response in 46.11s (~2844.32tok/s)
[7 ] [2026-04-09_08-49-21] JSON Error during parsing: Expecting value: line 1 column 1 (char 0)
```

Pattern repeats 1054+ times.

## Impact
- Bot stuck, cannot process new requests
- Wasting server resources (CPU/memory)
- User story generation failed
- Generation log: `~/AIStoryWriter-datacrytals/Logs/Generation_2026-04-08_11-50-00/Main.log`

## Solution Required

### Immediate Actions (COMPLETED)
1. ✅ Killed the stuck Write.py process (PID 3626588)
2. ✅ TelegramBot.py still running normally (PID 3056641)
3. ✅ Bot is now ready to accept new requests

### Code Fixes Required (COMPLETED)
1. ✅ Added MAX_RETRY_ATTEMPTS constant to Config.py (set to 10)
2. ✅ Modified `SafeGenerateText()` to break after max retries with proper error handling
3. ✅ Modified `SafeGenerateJSON()` to break after max retries with proper error handling
4. ✅ Added retry counter display in log messages (e.g., "Attempt 3/10")
5. ✅ Both functions now raise Exception after max retries instead of looping forever

### Remaining Recommendations (Optional Improvements)
1. Add context length validation BEFORE calling model
2. Implement context truncation strategy when too large
3. Add early warning when context > 50% of model limit
4. Implement context windowing/summarization for long stories
5. Consider using models with larger context windows for long stories

## Files to Modify (COMPLETED)
- ✅ `AIStoryWriter/Writer/Interface/Wrapper.py` (added retry limits)
- ✅ `AIStoryWriter/Writer/Config.py` (added MAX_RETRY config)

## Deployment Status
- ✅ Fixed files copied to server at `/home/netviet/AIStoryWriter-datacrytals/`
- ✅ TelegramBot restarted with new code (PID: 3211850)
- ✅ Bot is running and ready to accept new requests

## Testing Recommendations
1. Send a test story generation request to the bot
2. Monitor the log file for proper retry behavior
3. Verify that if retries exceed 10, the bot fails gracefully with error message
4. Check that context length warnings are still logged

## Server Location
- Server: 192.168.1.15
- User: netviet
- Project path: `/home/netviet/AIStoryWriter-datacrytals/`
- Bot PID: 3211850
- Log directory: `~/AIStoryWriter-datacrytals/Logs/`
