Docker Mailserver quick reference
Config root on this host: `/data/dms`.
## File formats

### postfix-accounts.cf
- Purpose: list of mailbox accounts and their password hashes.
- Location: `/data/dms/postfix-accounts.cf`.
- Format: one account per line as `email@domain|{SHA512-CRYPT}hash`.
- Example:
  ```
  user1@example.com|{SHA512-CRYPT}$6$salt$abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef/
  ```

### postfix-virtual.cf
- Purpose: alias and forward mappings.
- Location: `/data/dms/postfix-virtual.cf`.
- Format: one alias per line as `alias@domain recipient@domain`. Each alias-recipient pair must be on its own line; do not chain multiple pairs on the same line.
- Example:
  ```
  info@example.com mailbox@example.com
  sales@example.com mailbox@example.com
  ```
- Notes: multiple recipients are not supported on a single line; create separate lines for each destination if you need fan-out. Manage via `setup alias add|del|list`.

### dovecot-quotas.cf
- Purpose: per-user storage quotas.
- Location: `/data/dms/dovecot-quotas.cf`.
- Format: `email@domain:SIZE`, where size suffixes are `B` (byte), `K` (kibibyte), `M` (mebibyte), `G` (gibibyte), `T` (tebibyte).
- Example:
  ```
  user1@example.com:15G
  billing@example.com:302M
  ```

## DKIM
Do it manually via commands