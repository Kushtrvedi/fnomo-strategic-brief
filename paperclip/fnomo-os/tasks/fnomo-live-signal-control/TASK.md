---
name: "Task Type: fnomo_live_signal_controller"
assignee: "live-signal-controller"
project: "fnomo-operating-system"
---

Input:

- live run issue
- batch list
- channel split
- CRM writeback rules
- reply feed

Process:

- track sends
- run first signal control for sends 1-10 without changing messages
- verify writeback
- verify execution proof from the FNO-62 ledger and execution history
- classify replies
- flag issues
- run fail-safe control for send, CRM, reply-delay, partial execution, and monitor failures
- run coordination control for channel ownership, duplicate prevention, CRM locks, and reply ownership
- trigger metrics report

Output:

- progress
- replies and classification
- issues
- immediate next action
- fail-safe check
- coordination check
- first signal check
- execution proof
