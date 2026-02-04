import subprocess

def _run_enject_logic(filter_condition: str) -> bool:
    """
    Method for starting flash drive ejection.
    """
    ps_command = f"""
    $Eject = New-Object -ComObject Shell.Application;
    $volumes = Get-CimInstance -ClassName Win32_Volume | 
               Where-Object {{ $_.DriveType -eq 2 -and $_.DriveLetter -and {filter_condition} }};
    if ($volumes) {{
        foreach ($vol in $volumes) {{
            $Eject.NameSpace(17).ParseName($vol.DriveLetter).InvokeVerb('Eject');
            Write-Host "Ejected: $($vol.DriveLetter)"
        }}
    }} else {{ throw "No matching drives found" }}
    """

    try:
        process = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy", "Bypass",
                "-Command", ps_command
            ],
            capture_output=True, text=True, encoding="cp866",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return process.returncode == 0
    except Exception:
        return False

def eject_all() -> bool:
    return _run_enject_logic("$true")

def eject_by_letter(letter: str) -> bool:
    """
    Ejects a specific drive identified by its drive letter.

    The function normalizes the input, so both "E" and "e": are valid.

    Args:
        letter (str): The drive letter (e.g., "E", "E:", or " e ").
    
    Returns:
        bool: True if the specific drive was successfully ejected, False otherwise.
    """
    clean_letter = letter.strip().replace(":", "").upper()
    return _run_enject_logic(f"$_.DriveLetter -eq '{clean_letter}:'")

if __name__ == "__main__":
    if eject_all():
        print("Success: Drives ejected.")
    else:
        print("Notice: No drives to eject or error occurred.")
