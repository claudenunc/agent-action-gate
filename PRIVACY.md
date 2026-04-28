# Privacy Policy — Agent Action Gate

**Operator:** Nathan Michel (Sole Proprietor), Hardin, Kentucky, USA
**Effective:** 2026-04-26

This privacy policy covers two surfaces:
1. The Agent Action Gate open-source software project (this repository).
2. The associated SMS / messaging operations sent from the operator's Twilio number to the operator's own phone for personal AI-agent automation purposes.

## 1. Software project (this repository)

The Agent Action Gate code does not collect any personal data, telemetry, or analytics. It runs locally on the user's machine. There is no server, no account, no logging endpoint operated by the project author.

Users who run the software process their own data on their own infrastructure. Any personal data they handle is governed by their own privacy practices, not by this project.

## 2. Messaging operations (Twilio SMS)

The operator (Nathan Michel) operates a Sole Proprietor messaging campaign on Twilio. The campaign sends SMS messages **only to the operator's own personal phone number**. No third-party recipients are messaged.

### What information is collected

- Phone number of recipient (the operator's own number).
- Message content (sent and received).
- Timestamps and delivery status from Twilio.

### How information is used

- To deliver agent automation status, alerts, and approval requests to the operator's phone.
- To receive operator replies (yes/no/undo/reset commands) routing back into the agent system.

### Sharing

- Information is not sold, shared, or marketed.
- Twilio (the SMS carrier) processes messages as required to deliver them. Twilio's privacy policy applies to data Twilio handles: https://www.twilio.com/legal/privacy

### Retention

- Operator's local logs may retain message metadata indefinitely for personal record-keeping.
- Twilio retains message data per their retention policy.

### Opt-out

- The operator is the sole recipient and may opt out at any time by replying STOP to any message, or by disabling the system.

## 3. Contact

For privacy questions, contact: foolishnessenvy@gmail.com

## 4. Changes

This policy may be updated as the project evolves. Material changes will be reflected in this file's commit history in the public repository.
