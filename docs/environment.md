# Windows environment inspection

Measured on 2026-09-22 (Asia/Calcutta); memory and free space change with running apps.

| Item | Observed |
|---|---|
| OS | Windows 11 Home Single Language, 10.0.26200, 64-bit |
| CPU | AMD Ryzen 5 3500U with Radeon Vega Mobile Gfx |
| RAM visible to Windows | 6,237,040 KiB, about 5.95 GiB |
| Initially free physical RAM | 578,908 KiB, about 0.55 GiB |
| C: initially free | 4,762,562,560 bytes, about 4.44 GiB |
| D: initially free | 491,627,139,072 bytes, about 458 GiB |
| Python launcher installations | 3.13 (default), 3.12, 3.11 |
| Chosen isolated interpreter | Python 3.11.1, 64-bit, `.venv/Scripts/python.exe` |
| Git | 2.39.1.windows.1 |

The user reports 8 GB installed RAM and integrated Vega 8 graphics; usable RAM
reported by Windows is smaller. All milestone operations use the CPU. No GPU,
CUDA or model environment was installed. Scans live on D: to protect C: space.

Re-run the inspection in native PowerShell:

```powershell
Get-CimInstance Win32_OperatingSystem |
    Select-Object Caption, Version, OSArchitecture, TotalVisibleMemorySize, FreePhysicalMemory
Get-CimInstance Win32_Processor | Select-Object Name
Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free
py -0p
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "from mirai_ct.volume import memory_status; print(memory_status())"
git --version
git status --short --branch
git remote -v
```

Close unused apps before plotting. Notebook memory readings are process working
set/system-available snapshots, not exact peak allocation measurements. The reader
budgets its slice plus storage-slab buffers and rejects an oversized request.
