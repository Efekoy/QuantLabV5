#Requires -RunAsAdministrator
<#
QuantLabV5 -- HARD (OS-level) data isolation. Run ONCE, manually, as Administrator:

    powershell -ExecutionPolicy Bypass -File tools\harden_isolation.ps1

(Ported from QuantLabV4 tools/harden_isolation.ps1; V5 paths, user and deny list.)

It was NOT run automatically during the V5 bootstrap because it creates a Windows
account and needs a password that only you should choose.

What it does
  1. Creates a standard (non-admin) local user for V5 research (you type the password).
     Refuses if that user is an Administrator or a member of CodexSandboxUsers (that group
     has Modify on the Desktop and on the raw Quant\data folder).
  2. Grants the user READ+EXECUTE on the QuantLabV5 project (code, config, DISCOVERY data),
     and MODIFY only on ledgers\, results\, reports\, freezes\ (research outputs + ledger).
  3. Adds explicit DENY for the user on:
       C:\QuantLabV5_Vault                  (sealed partitions + LIVE_FORWARD)
       ...\Desktop\Quant\data               (raw full-history NQ/ES files)
       ...\Desktop\QuantLabV2, V3, V4, C:\QuantLabV3_Vault, C:\QuantLabV4_Vault (earlier labs)
     The vault is already restricted to Administrators + SYSTEM by the bootstrap.
  4. Allows the user to log on via Remote Desktop (so research sessions can run as it).
  5. VERIFIES, running AS the new user: every vault file and raw source must be DENIED by
     Windows and DISCOVERY must still load -> results\ISOLATION_CHECK_<user>.json

Nothing is deleted. No data file is modified. Existing ACEs for other accounts are untouched.

Known limitation (documented in docs/OS_ISOLATION.md): the research user can write the
ledger; edits are detected by the hash chain, and freezes pin ledger anchors, but a
research user could in principle delete the ledger outright. Keep periodic copies of
ledger anchors somewhere the research user cannot write (the vault).
#>
param([string]$User = "qlv5research")
$ErrorActionPreference = "Stop"
$Project = "C:\Users\Administrator\Desktop\QuantLabV5"
$Vault   = "C:\QuantLabV5_Vault"
$Python  = "C:\Program Files\Python312\python.exe"
$Deny    = @($Vault, "C:\Users\Administrator\Desktop\Quant\data", "C:\Users\Administrator\Desktop\QuantLabV2",
             "C:\Users\Administrator\Desktop\QuantLabV3", "C:\QuantLabV3_Vault",
             "C:\Users\Administrator\Desktop\QuantLabV4", "C:\QuantLabV4_Vault")

# 1. research user --------------------------------------------------------------------------
if (-not (Get-LocalUser -Name $User -ErrorAction SilentlyContinue)) {
    $pw = Read-Host -AsSecureString "Choose a password for the new research user '$User'"
    New-LocalUser -Name $User -Password $pw -FullName "QuantLabV5 research" `
        -Description "QuantLabV5 discovery - no access to sealed data" -PasswordNeverExpires | Out-Null
    Add-LocalGroupMember -SID "S-1-5-32-545" -Member $User            # BUILTIN\Users
    Write-Host "created user $User"
}
$admins = Get-LocalGroupMember -SID "S-1-5-32-544" | ForEach-Object { $_.Name.Split('\')[-1] }
if ($admins -contains $User) { throw "$User is an Administrator -- hard isolation impossible." }
if (Get-LocalGroup -Name "CodexSandboxUsers" -ErrorAction SilentlyContinue) {
    $sb = Get-LocalGroupMember -Name "CodexSandboxUsers" | ForEach-Object { $_.Name.Split('\')[-1] }
    if ($sb -contains $User) { throw "$User is in CodexSandboxUsers, which can modify the raw data folder." }
}
try { Add-LocalGroupMember -SID "S-1-5-32-555" -Member $User } catch { }   # Remote Desktop Users

# 2. project permissions ----------------------------------------------------------------------
icacls $Project /grant "${User}:(OI)(CI)RX" /T /C /Q | Out-Null
foreach ($d in @("ledgers", "results", "reports", "freezes")) {
    icacls (Join-Path $Project $d) /grant "${User}:(OI)(CI)M" /T /C /Q | Out-Null
}
# 3. explicit denies ---------------------------------------------------------------------------
foreach ($d in $Deny) {
    if (Test-Path $d) { icacls $d /deny "${User}:(OI)(CI)F" | Out-Null; Write-Host "DENY $User on $d" }
}

# 5. verification AS the research user ---------------------------------------------------------
$cred = Get-Credential -UserName $User -Message "Password for $User (runs the isolation check as that user)"
$out  = Join-Path $Project "results\ISOLATION_CHECK_${User}.stdout.txt"
$err  = Join-Path $Project "results\ISOLATION_CHECK_${User}.stderr.txt"
$p = Start-Process -FilePath $Python -ArgumentList "tools\check_isolation.py" -WorkingDirectory $Project `
        -Credential $cred -LoadUserProfile -Wait -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
Get-Content $out
if ($p.ExitCode -eq 0) {
    Write-Host "`nHARD DATA ISOLATION ACTIVE for $User (sealed + raw files denied by Windows; DISCOVERY readable)." -ForegroundColor Green
} else {
    Write-Host "`nNOT VERIFIED (exit $($p.ExitCode)). See $err" -ForegroundColor Red
    exit 1
}
