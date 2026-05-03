---
name: "Task Type: fnomo_system_health_monitor"
assignee: "system-health-monitor"
project: "fnomo-operating-system"
---

Input:

- Paperclip active task list
- FNOMO_MASTER_PIPELINE snapshot
- FNOMO_EXECUTION_TASKS snapshot
- FNOMO_EXECUTION_HISTORY snapshot
- Dashboard metrics

Process:

- Check Paperclip task progression.
- Check pipeline movement.
- Enforce follow-up SLA.
- Check outreach/follow-up quality.
- Check founder activation.
- Create corrective task if movement is blocked.

Output:

- System status
- Issue if any
- Correction applied
- Next priority

Run start of day, mid-cycle, and end of day.
