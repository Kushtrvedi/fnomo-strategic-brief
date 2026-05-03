---
name: "Task Type: fnomo_reply_handler"
assignee: "reply-handler-agent"
project: "fnomo-operating-system"
---

Input:

- Incoming reply
- Lead context
- Current stage
- Previous interaction

Process:

- Classify: Interested, Curious, Objection, or Not Relevant.
- Move stage according to classification.
- Generate next-step response.

Output:

- Classification
- Suggested stage movement
- Response
- Next action date

This is a task template. Create one child task per real reply.
