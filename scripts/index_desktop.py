#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description="Scan Windows desktop drives and ingest to remote Postgres")
    parser.add_argument(
        "--roots", 
        nargs="+", 
        default=["C:\\Users\\manni", "D:\\"],
        help="Directories to scan (default: C:\\Users\\manni D:\\)"
    )
    parser.add_argument(
        "--dsn",
        default="postgresql://ssot:.BvA%3A9h8t%3AyYrSm%200@192.168.1.50:5432/ssot",
        help="Database connection DSN"
    )
    args = parser.parse_args()

    # Filter out non-existent roots
    valid_roots = [r for r in args.roots if Path(r).exists()]
    if not valid_roots:
        print(f"Error: None of the specified roots exist: {args.roots}")
        sys.exit(1)

    print(f"Valid roots to scan: {valid_roots}")

    # Step 1: Run the scan
    temp_state = Path.home() / "AppData" / "Local" / "Temp" / "ssot_scan_state.json"
    output_dir = project_root / "scan_results"
    
    print("\n--- Starting Scan ---")
    scan_cmd = [
        sys.executable,
        str(project_root / "scanner" / "full_scan.py"),
        *valid_roots,
        "--state-path", str(temp_state),
        "--output-dir", str(output_dir)
    ]
    
    # We run the scanner as a subprocess and stream its output
    try:
        process = subprocess.Popen(scan_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            print(line, end="")
        process.wait()
        if process.returncode != 0:
            print(f"Error: Scanner failed with return code {process.returncode}")
            sys.exit(process.returncode)
    except Exception as e:
        print(f"Failed to execute scanner: {e}")
        sys.exit(1)

    print("\n--- Scan Completed! ---")

    # Step 2: Find the generated manifest file
    jsonl_files = sorted(
        output_dir.glob("scan_manifest_*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if not jsonl_files:
        print("Error: No scan manifest file found in output directory.")
        sys.exit(1)
        
    latest_manifest = jsonl_files[0]
    print(f"Latest scan manifest: {latest_manifest}")

    # Step 3: Run the ingestion
    print("\n--- Starting Ingestion to Remote Database (srv1: 192.168.1.50) ---")
    ingest_cmd = [
        sys.executable,
        str(project_root / "scripts" / "ingest_jsonl.py"),
        str(latest_manifest),
        "--dsn", args.dsn
    ]
    
    try:
        process = subprocess.Popen(ingest_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            print(line, end="")
        process.wait()
        if process.returncode != 0:
            print(f"Error: Ingestion failed with return code {process.returncode}")
            sys.exit(process.returncode)
    except Exception as e:
        print(f"Failed to execute ingestion: {e}")
        sys.exit(1)

    print("\n--- Ingestion Completed Successfully! ---")

if __name__ == "__main__":
    main()
