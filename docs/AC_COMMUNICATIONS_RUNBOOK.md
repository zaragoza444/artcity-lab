# AC Communications runbook

Art City staff send approved WhatsApp template messages from this studio. The sender is the official Meta Cloud API. Dashboard tokens are never shown. A stored phone number is not consent.

## Open decisions

These are not resolved by the software:

- Existing +964 number versus a separate API number
- Iraq coexistence eligibility and any provider fee
- Live portfolio messaging tier
- Meta approval of English, Arabic, Sorani, and Badini templates
- Evidence quality of the real contact file
- Privacy notice and retention sign-off
- Finance spend ceiling

Until those are signed, keep `COMM_LIVE_SEND_ENABLED=false`.

## Local run

1. `docker compose up -d`
2. `alembic upgrade head` from `backend/`
3. `python -m app.comm_worker` for dispatch when `COMM_PROCESS_INLINE=false`
4. Open `/communications`

`COMM_PROCESS_INLINE=true` lets the API drain a small batch during schedule. Production should set it false and run the worker.

## Add a sender

Administration is limited to a communications super admin. Create the sender with the E.164 number and the Meta phone number id. The access token stays in `META_ACCESS_TOKEN`. The rotate-token route always refuses dashboard edits.

## Rotate a token

1. Pause dispatch.
2. Replace `META_ACCESS_TOKEN` in the secret manager.
3. Redeploy the API and worker.
4. Call sender health and confirm `token` is still null in the response.

## Verify the webhook

Public URL: `POST /api/v1/communications/integrations/whatsapp/webhook`

Set the same path as the Meta callback. `GET` returns `hub.challenge` only when `hub.verify_token` matches `META_VERIFY_TOKEN`. `POST` requires `X-Hub-Signature-256` over the raw body. Invalid signatures are rejected. Duplicate payloads are stored once.

## Import contacts

CSV or XLSX. Required phone column `phone_number`. Consent is granted only when status, timestamp, source, and proof reference are all present. A spreadsheet cell that says granted without those fields is stored as unconfirmed and cannot be marketed. Existing opt-outs stay suppressed.

## Launch and pause

1. Register or sync an approved template. Do not relabel its Meta language.
2. Build a segment.
3. Preview exclusions, samples, and the quote.
4. A different user approves.
5. Schedule. Quiet hours default to 21:00–09:00 Asia/Baghdad.
6. When live send is on, the first batch is a test batch. Release production only after an accepted test message.
7. Pause withdraws queued work. Messages Meta already accepted can still be delivered.

## Reconcile cost

Delivered webhooks write provisional ledger rows. They do not change when an invoice arrives. Upload the invoice total with `POST /billing/reconcile`. The difference is a new adjustment row. Repeating the same invoice reference does not add another row.

## Incidents

| Situation | Action |
| --- | --- |
| Unexpected spend | Pause campaigns. The daily cap and campaign reserve already stop new sends. |
| Quality drop | Marketing dispatch pauses on red or low quality. |
| HTTP 429 | The worker backs off. Do not add numbers to get around the limit. |
| Webhook down | Pause new dispatch until receipts are trusted. |
| Token compromise | Remove the secret, rotate it at Meta, review the audit log. |
| Unknown send timeout | The recipient is quarantined and is not resent. |
| Consent doubt | Stop that audience. Suppression blocks the next attempt. |

## Restore

Take a daily encrypted Postgres backup. A restore must bring back contacts, suppressions, campaigns, and the cost ledger. RPO target is 24 hours and RTO target is 4 hours. Practice the restore before the first paid campaign.

## Worker

`python -m app.comm_worker` is separate from `python -m app.worker` so video jobs do not block WhatsApp dispatch.
