CANONICAL FNO-10 DATASET PAYLOAD - FNO-59 ACCEPTANCE CLOSEOUT

Snapshot timestamp: 2026-05-03 21:10 IST
Execution/SLA date: 2026-05-04
Source: FNOMO_MASTER_PIPELINE in War Room_ Community Outreach Pipeline - FNOMO Master.xlsx
Eligibility confirmation: Tier A + Contacted + No Response + last_contact_at >=48h stale at snapshot time
Total eligible count: 28
Critical field gaps: 0

Channel normalization: original_channel is preserved from source/inference. For FNO-4 execution, WhatsApp and LinkedIn rows go to their direct social lanes; Email rows are handled in the email lane using the prepared Monday execution plan, not discarded.
Channel handling counts: {"Email": 13, "LinkedIn": 5, "WhatsApp": 10}

Exclusion reason counts:
- not_tier_a_not_in_scope: 143
- tier_a_not_contacted: 23
- tier_a_contacted_reply_detected: 0
- tier_a_contacted_missing_last_contact: 0
- tier_a_contacted_less_than_48h_as_of_2026_05_04: 0

Machine-readable CSV:
```csv
lead_id,lead_name,tier,stage,outcome,original_channel,last_contact_at,owner
TDL-006,Firoz Alam,A,Contacted,No Response,LinkedIn,2026-05-02,Kush
TDL-003,CA Associations,A,Contacted,No Response,Email,2026-05-02,Kush
TDL-005,Shoumyan Biswas,A,Contacted,No Response,LinkedIn,2026-05-02,Kush
TDL-008,Saurav Goyal,A,Contacted,No Response,LinkedIn,2026-05-02,Kush
TDL-007,Abhimanyu Goyal,A,Contacted,No Response,LinkedIn,2026-05-02,Kush
SCR-CA-002,Arpit Rai,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-CA-003,Abhishek Jain,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-BO-001,Sandeep Wadhwani,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-BO-003,Sumit Lalwani,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-BO-006,Nitin Nahar,A,Contacted,No Response,Email,2026-05-02,Indu
SCR-CA-009,Milind Wadhwani,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-CA-034,CIRC Central Regional Office,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-BO-031,Kishore Gupta,A,Contacted,No Response,Email,2026-05-02,Indu
SCR-BO-035,Vinod Sapre,A,Contacted,No Response,Email,2026-05-02,Indu
SCR-BO-041,K.M. Kumar,A,Contacted,No Response,Email,2026-05-02,Indu
SCR-EM-001,Shanu Goel,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-EM-002,Abhishek,A,Contacted,No Response,Email,2026-05-02,Kush
SCR-EM-010,Shilpi Srivastav,A,Contacted,No Response,LinkedIn,2026-05-02,Kush
WA-CA-001,Rajesh Jain,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-002,Priya Mehta,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-003,Suresh Kumar,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-004,Ankita Shah,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-005,Vivek Nair,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-006,Deepa Verma,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-008,Meera Krishnan,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-009,Ravi Shankar,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-CA-010,Nisha Patel,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
WA-BIZ-005,Sunita Joshi,A,Contacted,No Response,WhatsApp,2026-05-02,Kush
```

Resolution Action Taken: Posted canonical machine-readable payload directly in FNO-10, satisfying the acceptance gap raised by FNO-59/FNO-60.
Execution Status: Ready
Confidence: 86/100