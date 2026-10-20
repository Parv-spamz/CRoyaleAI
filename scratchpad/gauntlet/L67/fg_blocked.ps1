# Is a blocking system dialog holding the foreground?
#
# L67cb: a Windows Security nag titled "Antivirus protection expired" (owned by explorer.exe) has
# now killed three live runs -- 2026-09-13, and twice on 2026-09-18. While it holds the foreground,
# play.py's navigator reads `game: False`, cannot force focus, and stops itself after 600 s with
# zero matches. It cannot be closed programmatically: WM_CLOSE and SC_CLOSE to both the foreground
# handle and its root ancestor, and SetForegroundWindow on the game window, were all tried and all
# failed. Only a human click, or the nag expiring on its own, clears it.
#
# Exit 1 = blocked (do not launch).  Exit 0 = clear (safe to launch).
# Prints the current foreground title either way.

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class FgChk {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  public static string Title(IntPtr h) { StringBuilder sb = new StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString(); }
}
"@

$t = [FgChk]::Title([FgChk]::GetForegroundWindow())
Write-Output "fg=$t"

if ($t -match 'Antivirus|protection expired|McAfee|Norton|Avast|AVG|Malwarebytes') {
    exit 1
}

# The game window must also still exist, or launching is pointless.
$g = Get-Process crosvm -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*Clash*' }
if (-not $g) {
    Write-Output "no-clash-window"
    exit 1
}

exit 0
