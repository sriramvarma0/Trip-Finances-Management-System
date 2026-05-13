taskkill /F /IM python.exe /T 2>$null
Start-Sleep -Seconds 1
Start-Process python -ArgumentList "app.py" -WorkingDirectory "C:\codebase\new_projects\Trip-Finances-Management-System" -NoNewWindow
Start-Sleep -Seconds 2
Write-Output "Server restarted on port 8000"
