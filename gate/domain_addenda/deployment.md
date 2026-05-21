# Deployment Addendum

This addendum applies when a gate run touches public-facing deployment routing, service ports, or production-traffic ownership.

Checks required by this addendum:
- production routing topology must be inventoried (read-only) before any change;
- cutover risk must be classified (LOW_RISK_PROCEED | MEDIUM_RISK_DEFER_RECOMMENDED | HIGH_RISK_DEFER | BLOCKER) with explicit evidence;
- if cutover proceeds: backup of prior service config, smoke checks (curl, systemd status), and rollback procedure must be documented and verified;
- if cutover is deferred: planned port + planned notice content + prerequisites for future cutover must be documented;
- no kill of long-lived services without explicit user go-ahead;
- secrets (env vars, cert keys, tokens) must not appear in any package report.
