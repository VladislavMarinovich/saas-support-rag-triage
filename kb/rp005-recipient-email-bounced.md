# RP005 — Recipient email bounced

Polaris shows RP005 when a specific recipient's mail server permanently rejected a report. Other recipients on the same report still receive it.

## What RP005 tells you about that address

RP005 is a hard bounce reported back by the receiving server, not a guess. Usual reasons: the mailbox was closed, the person left the company, the domain no longer accepts mail, or the address was mistyped when the report was set up.

After repeated bounces to the same address, Polaris stops attempting delivery to it so your sending reputation is not damaged, and marks it in the report's recipient list.

## How to fix RP005

1. Open **Reports**, select the report, and find the address marked as bounced.
2. Replace it with a current address, or remove it if the person no longer needs the report.
3. If the address should work, ask the recipient's IT team whether mail from `reports@polaris.io` is being rejected at the gateway.
4. Save and use **Send now** to confirm the new address is accepted.

If the address is valid, accepts mail from elsewhere, and still bounces from Polaris, contact support with the report ID and the full address.
