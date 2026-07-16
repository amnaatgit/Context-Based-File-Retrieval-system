# Cloud Infrastructure Overview

## Summary
This document describes the current cloud infrastructure that hosts the retrieval platform and internal services. It is maintained by the Infrastructure team and complements the server migration plan and incident playbook.

## Environments
- Production: serves live traffic, autoscaled, monitored 24/7
- Staging: mirror of production for pre-release testing
- Development: shared environment for engineering work

## Core Components
1. Application servers running the FastAPI backend
2. Managed PostgreSQL database with daily backups
3. Object storage for uploaded and ingested documents
4. CDN for static assets and cached responses
5. Monitoring and alerting stack

## Deployment Pipeline
Code merged to main triggers an automated build and deployment. Migrations run before the new version receives traffic. Rollback is a single command if health checks fail, as described in the incident playbook.

## Cost Optimization
- Right-size compute instances based on weekly usage
- Use reserved capacity for steady production workloads
- Move cold document storage to a cheaper storage tier after 90 days
- Review cloud spend monthly with the finance team

## Security
Network access is restricted by security groups. Secrets are stored in a managed vault, never in code. All infrastructure changes go through peer review.

## Disaster Recovery
Backups are tested quarterly. The recovery time objective is four hours and the recovery point objective is one hour.

Maintained by: Usman Tariq, Platform Engineer, Infrastructure
