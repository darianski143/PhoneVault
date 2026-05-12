import sys
import time
from pathlib import Path
import subprocess
from datetime import datetime

RUN_EVERY = 5
CYCLES = 5

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports.py"
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = OUT_DIR / "audit.log"

def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    LOG_PATH.write_text(LOG_PATH.read_text(encoding="utf-8") + line if LOG_PATH.exists() else line, encoding="utf-8")
def main():
    print("AUTO REPORT START")
    print("reports.py: ", REPORTS)
    print("outputs: ", OUT_DIR)
    for i in range(1, CYCLES + 1):
        log(f"Cycle: {i} started")
        res = subprocess.run(
            [sys.executable, str(REPORTS)],
            cwd = str(ROOT),
            capture_output = True,
            text = True
        )

        print(f"\n=== Cycle {i} ===")
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print("STDERR:\n", res.stderr)
        if res.returncode != 0:
            log(f"Cycle {i} FAILED (code={res.returncode})")
            break
        else:
            log(f"Cycle {i} finished okay")

        time.sleep(RUN_EVERY)

    print("AUTO REPORT END")

if __name__ == "__main__":
    main()