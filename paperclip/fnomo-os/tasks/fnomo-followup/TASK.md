---
name: "Task Type: fnomo_followup"
assignee: "follow-up-agent"
project: "fnomo-operating-system"
---

Input:

- Lead context
- Last contact date
- Last message context
- Channel
- Stage and outcome

Process:

- If Contacted and no reply after 48h, create Follow-up 1.
- If no reply after 4 days, create Follow-up 2.
- If no reply after 7 days, escalate or mark cold.

Output:

- Follow-up message
- Stage impact
- Next action
- Next action date

This is a task template. Create one child task per real lead when execution starts.
