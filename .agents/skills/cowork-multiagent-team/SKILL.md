---
name: cowork-multiagent-team
description: Multi-agent cooperative coworking architecture for autonomous project development. Enables specialist agents (Frontend, Backend, DevOps, Growth/Marketing) to collaborate, review each other's outputs, and deliver production software autonomously.
---

# Antigravity Cowork: Multi-Agent Collaborative Team System

The Cowork framework organizes AI agents into specialized virtual coworkers that work concurrently on complex SaaS features.

## 1. Virtual Coworker Roles

```
┌─────────────────────────────────────────────────────────────┐
│                    COWORK TEAM SQUAD                        │
├──────────────────────┬──────────────────────────────────────┤
│ 1. Tech Lead Agent   │ Architecture design, task delegation │
│ 2. Frontend Designer │ Sleek modern UI, responsive layout   │
│ 3. Backend Engineer  │ REST APIs, Auth, Database, Payments  │
│ 4. Automation Agent  │ Scrapers, PDF engine, Webhooks       │
│ 5. Growth & SEO Lead │ High-converting copy, pricing tables │
└──────────────────────┴──────────────────────────────────────┘
```

## 2. Cowork Communication Protocol

1. **State Synchronization:** Agents share common models in `core/` and communicate through structured JSON payloads.
2. **Review & Hand-off:**
   - Frontend Agent builds UI $\rightarrow$ Backend Agent connects endpoints $\rightarrow$ Automation Agent wires background queues.
3. **Automated Verification:** Every feature must pass regression tests in `test_pipeline.py` before closing task.
