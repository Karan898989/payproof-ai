#!/usr/bin/env python3
"""
PayProof AI — Master Single-Entrypoint Launcher
==============================================
Runs dependency checks, installs missing packages if necessary,
frees conflicting ports or finds an available port automatically,
initializes the database, seeds demo baseline cases, launches
the FastAPI backend, and automatically opens your web browser.
"""

import sys
import subprocess
import os
import time
import socket
import webbrowser
import threading
from pathlib import Path

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "pypdf",
    "yaml",
    "jinja2",
    "multipart",
    "httpx",
]

def check_and_install_dependencies():
    print("=" * 65)
    print("  PayProof AI — Pre-Payment Verification System")
    print("  Local-First • NVIDIA Nemotron • Cedar IAM Authorization")
    print("=" * 65)
    print("\n[1/4] Checking Python environment and runtime dependencies...")
    
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[*] Missing dependencies detected: {', '.join(missing)}")
        print("[*] Installing requirements automatically via pip...")
        req_file = Path(__file__).parent / "requirements.txt"
        if req_file.exists():
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        else:
            cmd = [sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "pypdf", "pyyaml", "jinja2", "python-multipart", "httpx"]
        
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print("[!] Error installing packages. Please ensure pip and internet access are available.")
            sys.exit(1)
        print("[+] All dependencies successfully installed.")
    else:
        print("[+] All runtime dependencies are satisfied.")

def ensure_initialized_and_seeded():
    print("\n[2/4] Initializing SQLite database and verifying baseline data...")
    # Add src to sys.path
    src_dir = Path(__file__).parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from payproof.repositories.db import init_db
    from payproof.repositories.case_repo import case_repo
    from payproof.config import settings

    init_db()

    # Seed if cases table is empty
    cases = case_repo.list_cases()
    if not cases:
        print("[*] Empty database detected. Seeding Demo Scenarios A, B, and C...")
        from scripts.seed_data import seed_all
        import asyncio
        asyncio.run(seed_all())
        print("[+] Demo scenarios seeded into .var/payproof.db.")
    else:
        print(f"[+] Existing database found with {len(cases)} verification cases.")

def check_nvidia_configuration():
    print("\n[3/4] Inspecting NVIDIA Nemotron configuration...")
    from payproof.config import settings
    from payproof.agents.nim_client import nim_client

    if nim_client.is_configured():
        masked = f"{settings.nvidia_api_key[:4]}...{settings.nvidia_api_key[-4:]}" if len(settings.nvidia_api_key) > 8 else "***"
        print(f"[+] NVIDIA NIM Configured: API key active ({masked})")
        print(f"    Model: {settings.nvidia_model}")
        print(f"    Endpoint: {settings.nvidia_base_url}")
    else:
        print("[i] NVIDIA_API_KEY is not set (or empty).")
        print("    System will operate in DETERMINISTIC MODE.")
        print("    You can enter your API key anytime in the Web UI Settings modal.")

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def free_port_if_in_use(port: int) -> bool:
    if not is_port_in_use(port):
        return True

    print(f"[*] Port {port} is occupied by an existing process. Terminating lingering process...")
    try:
        if sys.platform == "win32":
            output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode(errors="ignore")
            pids = set()
            for line in output.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in parts[3].upper():
                    pids.add(parts[4])
                elif len(parts) >= 4 and parts[1].endswith(f":{port}"):
                    pids.add(parts[-1])
            for pid in pids:
                if pid and pid != "0":
                    print(f"[*] Terminating PID {pid} on port {port}...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.0)
        else:
            subprocess.run(f"fuser -k {port}/tcp", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.0)
    except Exception as e:
        print(f"[!] Note: Could not auto-terminate process on port {port}: {e}")

    return not is_port_in_use(port)

def resolve_available_port(preferred_port: int = 8000, host: str = "127.0.0.1") -> int:
    # First try to clear the preferred port
    if free_port_if_in_use(preferred_port):
        return preferred_port

    # If still occupied, search for next free port
    for p in range(preferred_port + 1, preferred_port + 25):
        if not is_port_in_use(p, host):
            print(f"[+] Found available alternate port: {p}")
            return p

    return preferred_port

def open_browser_delayed(url: str, delay: float = 1.5):
    time.sleep(delay)
    print(f"\n[+] Opening browser at: {url}")
    webbrowser.open(url)

def start_server():
    print("\n[4/4] Starting PayProof AI Web Server...")
    import uvicorn
    from payproof.config import settings

    host = settings.app_host
    preferred_port = settings.app_port
    
    # Resolve port conflicts automatically
    port = resolve_available_port(preferred_port, host)
    settings.app_port = port
    url = f"http://{host}:{port}"

    print("-" * 65)
    print(f"  Web Application Running at: {url}")
    print("  Press Ctrl+C to terminate.")
    print("-" * 65 + "\n")

    # Start browser in background thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    # Run Uvicorn
    uvicorn.run(
        "payproof.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    check_and_install_dependencies()
    ensure_initialized_and_seeded()
    check_nvidia_configuration()
    start_server()
