' ==============================================================================
' OmniSwarm PC Hub Silent Background Launcher (Windows VBScript)
' Launches daemonize_hub.ps1 in hidden background mode with no console window.
' Can be placed directly into shell:startup (%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup)
' ==============================================================================

Dim WshShell, FSO, strDir, strCmd
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & strDir & "\daemonize_hub.ps1"" start"

' 0 = Hide window, False = Return immediately without waiting
WshShell.Run strCmd, 0, False
