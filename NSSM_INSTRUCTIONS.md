NSSM (Windows service) setup instructions

1) Download NSSM
   - https://nssm.cc/download
   - Extract nssm.exe to a convenient folder (e.g., C:\tools\nssm)

2) Install service via GUI or CLI
   - GUI: run `nssm install MMRBot`, set Path to your python.exe in venv, set Arguments to the path to `bot.py` or set Application to powershell and arguments to run `run_bot.ps1`.
   - CLI example:
     C:\tools\nssm\nssm.exe install MMRBot "C:\Users\kks\Desktop\bot\.venv\Scripts\python.exe" "C:\Users\kks\Desktop\bot\bot.py"

3) Set environment variables (if needed)
   - In NSSM GUI -> Environment add: DISCORD_TOKEN (not recommended to save token here in plain text; prefer run_bot.ps1 prompting) and ENABLE_PRIVILEGED_INTENTS=1 if required.

4) Start service
   - C:\tools\nssm\nssm.exe start MMRBot

5) Logs
   - NSSM provides stdout/stderr redirection settings; set to files for troubleshooting.

6) Remove service
   - C:\tools\nssm\nssm.exe remove MMRBot confirm

Notes:
- Running as a service with a token saved in environment variables is convenient but store your token securely. Consider using a secure secrets manager in production.
