# Load Testing Guide

This guide explains different types of performance tests and how to run them using Locust.

## Test Types Overview

| Type               | Purpose                                 | Duration\* | Load Pattern           |
|--------------------|-----------------------------------------|------------|------------------------|
| **Load**           | Verify system handles expected traffic  | 5-15 min   | Steady, expected users |
| **Stress**         | Find breaking point                     | 10-20 min  | Gradually increasing   |
| **Spike**          | Test sudden traffic surges              | 5-10 min   | Sudden bursts          |
| **Soak**           | Find memory leaks, degradation          | 1-4 hours  | Steady, extended       |
| **Error Recovery** | Verify graceful failure & bounce-back   | 5-15 min   | Chaos injection        |

\*Duration and user count are relative and should be adjusted based on system characteristics.

---

## Load Testing

**Goal**: Verify the system handles expected concurrent users.

```bash
# Simulate 50 concurrent users, ramping up 10 users/second
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

**What to look for**:
- Response times remain consistent
- Error rate stays near 0%
- Throughput matches expectations

---

## Stress Testing

**Goal**: Find the system's breaking point by gradually increasing load.

```bash
# Start with 10 users, manually increase via web UI
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 10 \
  --spawn-rate 5

# Or use step load pattern (add 50 users every 2 minutes)
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 500 \
  --spawn-rate 1 \
  --run-time 20m \
  --headless
```

**What to look for**:
- At what user count do response times degrade?
- When do errors start appearing?
- What's the maximum throughput?

---

## Spike Testing

**Goal**: Test system behavior under sudden traffic surges.

```bash
# Use the SpikeUser class for burst behavior
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 100 \
  --run-time 5m \
  --headless \
  --tags spike
```

**Spike simulation approach**:
1. Start with low user count (10 users)
2. Suddenly spawn 100+ users (via web UI or script)
3. Observe recovery time
4. Drop back to baseline

**What to look for**:
- Does the system recover after the spike?
- Are requests queued or dropped?
- How long until response times normalize?

---

## Soak Testing

**Goal**: Identify memory leaks, connection pool exhaustion, or gradual degradation.

```bash
# Run for extended period with moderate load
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 30 \
  --spawn-rate 5 \
  --run-time 2h \
  --headless \
  --csv=soak_results
```

**What to look for**:
- Memory usage over time (monitor server)
- Response time trends (should stay flat)
- Error rate trends
- Database connection count

---

## Error Recovery Testing

**Goal**: Verify the system fails gracefully and recovers when dependencies misbehave.

**Chaos to inject**:
- Kill database connections mid-request
- Simulate network timeouts
- Return 500s from downstream services
- Exhaust connection pools

**What to look for**:
- Are errors returned quickly (fail-fast) or do requests hang?
- Does the system recover automatically when dependencies return?
- Are partial failures handled (e.g., payment created but notification failed)?
- Do circuit breakers trip and reset appropriately?

---

## User Classes

The `locustfile.py` includes different user classes for different scenarios:

| Class         | Behavior                 | Use Case               |
|---------------|--------------------------|------------------------|
| `PaymentUser` | Steady payment creation  | Load/Soak testing      |
| `SpikeUser`   | Aggressive, no wait time | Spike testing          |
| `MixedUser`   | Varied operations        | Realistic load testing |

---

## Analyzing Results

### Out-of-the-Box CSV Output

Generate CSV reports by appending `--csv=results/load_test` to your Locust command.  
This creates:
- `load_test_stats.csv` - Aggregate statistics
- `load_test_stats_history.csv` - Time-series data
- `load_test_failures.csv` - Error details

TODO: instead of manually grokking CSVs, results should be sent to a time-series DB like InfluxDB or Prometheus for better analysis and visualization.  
This would also allow for baseline comparisons and alerting on regressions over time.

---

## System Monitoring Tools

While Locust measures client-side metrics (response times, throughput), server-side monitoring is equally important to get the full picture.

### Production-Grade Observability Stack

| Tool              | Purpose                    | Notes                                 |
|-------------------|----------------------------|---------------------------------------|
| **Prometheus**    | Metrics collection         | Time-series DB, pull-based            |
| **Grafana**       | Visualization & dashboards | Pairs with Prometheus                 |
| **InfluxDB**      | Time-series DB             | Alternative to Prometheus, push-based |
| **OpenTelemetry** | Traces, metrics, logs      | Vendor-neutral, unified observability |

### Key Metrics to Monitor

| Metric                 | Target           | Why                 |
|------------------------|------------------|---------------------|
| CPU Usage              | < 80%            | Headroom for spikes |
| Memory Usage           | Stable over time | Detect leaks        |
| Response Time p95      | < 500ms          | User experience     |
| Error Rate             | < 0.1%           | Reliability         |
| Open Connections       | Below limits     | Prevent exhaustion  |
| Event Loop Lag (async) | < 100ms          | Async health        |
