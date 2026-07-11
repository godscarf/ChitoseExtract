Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = appDir
' 0 = 完全隐藏窗口
shell.Run """" & appDir & "\launch.bat""", 0, False
