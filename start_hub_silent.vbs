' ==============================================================================
' OmniSwarm Silent Hub Launcher (Windows VBScript)
' Launches daemonize_hub.ps1 in the background with zero console window flash.
' Can be placed directly into shell:startup (%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup)
' ==============================================================================
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)

PsCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & ScriptDir & "\daemonize_hub.ps1"" start"
WshShell.Run PsCmd, 0, False
