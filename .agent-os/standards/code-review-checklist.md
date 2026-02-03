# Code Review Checklist

This checklist should be used for all code reviews and pull requests to ensure code quality and prevent common bugs.

## Critical Thread Safety Checks

### ❌ Double-Locking Anti-Pattern Detection

**ALWAYS check for these patterns when reviewing code that uses StateService:**

1. **Pattern to Flag:**
   ```python
   with state._frame_lock:
       state.latest_frame = value
   ```
   
2. **Pattern to Flag:**
   ```python
   with state._audio_lock:
       state.audio_muted = True
   ```
   
3. **Pattern to Flag:**
   ```python
   with state._gamepad_lock:
       state.gamepad_enabled = enable
   ```

4. **General Pattern:**
   ```python
   with state._<any>_lock:
       state.<any_property> = value  # ❌ DEADLOCK!
   ```

### ✅ Correct Patterns

**These patterns are SAFE:**

1. **Direct property access (PREFERRED):**
   ```python
   state.latest_frame = value  # ✅ Property handles locking
   ```

2. **Multiple property access:**
   ```python
   state.audio_muted = True
   state.audio_streaming_enabled = False
   # Each property handles its own lock
   ```

3. **Internal StateService methods using locks:**
   ```python
   # Inside StateService class only:
   def reset_audio_state(self):
       with self._audio_lock:
           self._audio_muted = True  # ✅ Direct attribute access
           self._audio_streaming_enabled = False
   ```

## Automated Checks

### Grep-based Linting

Run this command before committing to detect potential double-locking:

```bash
# Search for potential double-locking patterns
grep -n "with state\._.*lock:" web_interface.py app/**/*.py

# If this returns ANY results, review them carefully!
# Most cases are likely double-locking bugs.
```

### Python Script for Detection

```python
# scripts/check_double_locking.py
import re
import sys

def check_file(filepath):
    """Check file for double-locking anti-patterns."""
    issues = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        # Check for explicit lock usage with state object
        if re.search(r'with\s+state\._\w+_lock:', line):
            issues.append(f"Line {i}: Potential double-locking - {line.strip()}")
    
    return issues

if __name__ == '__main__':
    files = sys.argv[1:]
    all_issues = []
    
    for filepath in files:
        issues = check_file(filepath)
        if issues:
            print(f"\n{filepath}:")
            for issue in issues:
                print(f"  {issue}")
            all_issues.extend(issues)
    
    if all_issues:
        print(f"\n❌ Found {len(all_issues)} potential double-locking issues!")
        sys.exit(1)
    else:
        print("✅ No double-locking issues found!")
        sys.exit(0)
```

Usage:
```bash
python scripts/check_double_locking.py web_interface.py app/**/*.py
```

## General Code Review Checklist

- [ ] Code follows PEP 8 style guidelines
- [ ] All functions have docstrings
- [ ] Type hints are used for function parameters and return values
- [ ] No hardcoded credentials or secrets
- [ ] Error handling is appropriate
- [ ] Logging is used instead of print statements
- [ ] Unit tests are included for new functionality
- [ ] No double-locking patterns (see above)
- [ ] Thread-safe operations use appropriate locking
- [ ] Async functions don't call blocking operations directly
- [ ] Blocking I/O is wrapped in `asyncio.to_thread()`

