# OS-level isolation: current status and how to activate it

## Current status (V5 bootstrap, 2026-09-25): NOT ACTIVE for research

* The research process runs as `Administrator`, a member of BUILTIN\Administrators.
* The V5 sealed partitions are in `C:\QuantLabV5_Vault`, outside the project tree. The bootstrap reduced
  the vault's NTFS ACL to Administrators + SYSTEM and removed inheritance. That blocks every
  non-administrator account.
* **Code running as Administrator can still open vault files directly.** `tools/check_isolation.py`
  records this in `provenance/ISOLATION_CHECK_Administrator.json`. The only thing that stops research
  code is the software gate: load_view, the stage gate and the ledger. A static test forbids research code
  from opening data files or naming a vault.
* The earlier labs' data stores (`C:\QuantLabV4_Vault`, `C:\QuantLabV3_Vault`, and the V2/V3/V4 `data`
  folders) contain the same 2019-2026 periods. They are just as openable by Administrator.
  `load_view` refuses any registry path inside them, and the static test forbids naming them.
* Pre-existing condition, not changed by V5 (already reported by V4): `Desktop\Quant\data`, which holds the
  raw full-history files, grants Modify to `CodexSandboxUsers` and to one unresolved SID.

## Activating it (manual, needs your password choice)

```powershell
# as Administrator
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Desktop\QuantLabV5\tools\harden_isolation.ps1
```

The script creates the non-admin user `qlv5research` and grants it read on the project and write on
ledgers/results/reports/freezes. It adds explicit denies on the V5 vault, the raw data folder, the
V2/V3/V4 folders and the V3/V4 vaults. It then runs `tools/check_isolation.py` as that user. Isolation
is **active** only when `provenance/ISOLATION_CHECK_qlv5research.json` reports
`"os_isolation_active_for_this_account": true` and all research runs as `qlv5research`.

Note: denying the research user access to `Desktop\QuantLabV4` also denies V4's code. The V4-equivalence
tests (`tests/test_v4_equivalence.py`) then skip for that user, but still run for the administrator.

## Privileged operations that stay with the administrator

* the one-time partitioning (done);
* stage transitions whose preconditions need vault access (entering DISCOVERY is done);
* LIVE_FORWARD ingestion (`tools/ingest_live_forward.py`);
* reading the vault at VALIDATION and later stages. Those need either an administrator session or a
  later, explicit ACL change for the research account.

## Known limitations

* The research account must be able to append to the ledger, so it could delete the file outright.
  Edits, reordering and truncation are detected: the chain breaks and freezes pin ledger anchors.
  Deleting the whole ledger is caught by the stage gate's state/ledger cross-check, which then refuses
  every read.
* Software checks cannot stop an administrator.
