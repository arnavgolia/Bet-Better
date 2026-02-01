---
description: Run the Odds Ingestion Worker
---

1. Run the worker (runs continuously)
// turbo
docker-compose exec backend python -m scripts.odds_worker

2. Or run a single update (for testing)
// turbo
docker-compose exec backend python -m scripts.test_odds
