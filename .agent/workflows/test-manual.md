---
description: How to run the manual testing suite for oguild and guildpack
---

This workflow runs a comprehensive manual test of all `oguild` and `guildpack` functionalities within a Docker container.

### Pre-requisites
- Docker installed and running
- Docker Compose installed

### Steps

// turbo
1. Run the manual testing suite:
```bash
make test-manual
```

2. Observe the logs to ensure:
   - Dynamic logger detects the module names correctly.
   - `Ok` and `Error` responses are formatted as JSON.
   - `@police` decorator catches and handles exceptions.
   - `sanitize_fields` cleans sensitive data.
   - `guildpack` alias functions identically to `oguild`.

3. To clean up the persistent container:
```bash
docker compose down
```
