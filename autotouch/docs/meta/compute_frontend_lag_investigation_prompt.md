# Meta Prompt: Import Lag + Compute Constraints Investigation

You are an expert SRE + performance engineer. Your job is to triage a user‑visible lag issue after importing a large CSV (10,000 rows) into Smart Table. The symptom: frontend horizontal and vertical scrolling becomes very slow and choppy. Determine whether this is primarily a backend compute constraint or a frontend rendering/virtualization issue, and produce an actionable plan with the lowest‑cost fixes first.

## Context (Current Known State)
- Kubernetes cluster (AKS), 2 nodes: Standard_E4as_v6.
- API HPA recently hit max replicas and CPU target exceeded:
  - HPA target: 65% CPU of request
  - HPA max: 6 pods
  - Recent: CPU ~89% of request, scaled to max
  - Readiness probe failures around that time (timeout / connection refused on /healthz)
- API resource requests/limits (default namespace):
  - API: requests 200m CPU / 1Gi RAM, limits 600m CPU / 3Gi RAM
  - Celery: requests 200m / 1.25Gi, limits 400m / 2.5Gi
  - LLM: requests 400m / 2Gi, limits 800m / 3Gi
- `kubectl top nodes` shows nodes not saturated (CPU < 40%, memory ~30%).
- API logs show heavy Socket.IO event emission during column runs (cells_update_batch, cell_update, column_run_progress, credits_update).
- No obvious OOM/eviction logs in last ~25 minutes.

## Goal
Explain where compute is going and isolate whether the lag is:
1) Backend CPU/memory saturation, queuing, or slow queries, or
2) Frontend rendering/layout work (DOM size, virtualization gaps, reflow/paint), or
3) A mix (e.g., backend spamming real‑time updates that create frontend re-render storms).

## Required Output
Produce a concise diagnostic report with:
- Primary bottleneck hypothesis (backend vs frontend vs mixed) with evidence
- Specific signals checked (commands/logs/metrics)
- Low‑cost mitigation steps (ordered)
- Long‑term fixes (if needed)

## Investigation Playbook
### 1) Backend Compute Health
- Check HPA and scale events:
  - `kubectl get hpa -n default`
  - `kubectl describe hpa smart-table-api-hpa -n default`
- Check readiness/liveness events:
  - `kubectl get events -n default --sort-by=.metadata.creationTimestamp | tail -n 200`
- Check pod resource usage:
  - `kubectl top pods -n default`
  - `kubectl top nodes`
- Inspect API logs for slow requests / timeouts / large payloads:
  - `kubectl logs -n default deployment/smart-table-api-deployment --since=25m --all-containers=true`
  - Filter for `timeout|slow|latency|error|throttl|oom|memory|cpu|pressure`

### 2) Backend Workload Attribution
- Identify hotspots during import:
  - Upload/preview endpoints
  - Table data fetch endpoints
  - Socket.IO event emission volume
- Correlate with the import timeline:
  - When did the 10k import start/finish?
  - Did API CPU spike during scroll issues or only during import/preview?

### 3) Frontend Performance Signals
- Use browser Performance panel while scrolling:
  - If main thread > 16ms per frame with minimal network activity → frontend bottleneck
- Check for excessive DOM nodes:
  - Verify row + column virtualization
  - Confirm horizontal scroll does not render full column set
- Check render thrash:
  - Frequent re-render from Socket.IO updates
  - Recalculating widths or layout on scroll

### 4) Decision Criteria
- Backend bottleneck if:
  - API latency/timeout spikes align with UI lag
  - HPA hits max and readiness fails
  - Slow queries or heavy API responses during scroll
- Frontend bottleneck if:
  - Smooth network responses but janky main thread
  - Large DOM and non-virtualized horizontal scrolling
  - UI lag persists even after API is idle
- Mixed if:
  - Realtime updates flood UI and cause re-render storms

## Suggested Low-Cost Fixes (Prioritize)
1. Frontend virtualization fixes (row + column), memoization, reduce re-renders.
2. Debounce or batch realtime updates to UI (coalesce updates).
3. Increase API HPA max slightly (6 → 8/10) if API CPU hits max during imports.
4. Raise API CPU request to reduce throttling (e.g., 200m → 400m) if CPU pressure continues.

## Long-Term Fixes
- Add endpoint-level latency metrics and tracing for import/scroll load.
- Introduce backpressure on event emission during large batch updates.
- Separate websocket/event workloads into a dedicated worker (if needed).

## Questions to Answer
- What exact timestamp did the import start and when did the UI lag occur?
- Was the UI lag during ongoing column runs or after import completed?
- Is the table using row + column virtualization?
- What are typical API response sizes for table fetch on 10k rows?
- Are we emitting per-cell updates or batching effectively?

## Output Format
- 1–2 paragraphs of root cause reasoning
- Bullet list of evidence gathered
- Bullet list of immediate actions and longer-term changes
