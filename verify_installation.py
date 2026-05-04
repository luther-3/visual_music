#!/usr/bin/env python3
"""Verify required dependencies for the music visualizer project."""

import subprocess
import sys


def check_python_version() -> bool:
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    print(f"[FAIL] Python version too low: {version.major}.{version.minor}.{version.micro}")
    return False


def check_package(package_name: str) -> bool:
    try:
        module = __import__(package_name)
        version = getattr(module, "__version__", "unknown")
        print(f"[OK] {package_name} {version}")
        return True
    except ImportError:
        print(f"[FAIL] {package_name} is not installed")
        return False


def check_ffmpeg() -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout:
            print(f"[OK] {result.stdout.splitlines()[0]}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print("[WARN] ffmpeg not found in PATH (MP3 may not be supported)")
    return False


def main() -> int:
    print("Checking environment and dependencies...\n")

    all_ok = True
    all_ok &= check_python_version()

    print("\nRequired packages:")
    for pkg in ["numpy", "scipy", "librosa", "pygame", "soundfile", "audioread"]:
        all_ok &= check_package(pkg)

    print("\nBuiltin package:")
    try:
        import tkinter  # noqa: F401

        print("[OK] tkinter (builtin)")
    except ImportError:
        print("[FAIL] tkinter is not available")
        all_ok = False

    print("\nOptional package:")
    check_package("matplotlib")

    print("\nSystem dependency:")
    check_ffmpeg()

    print("\n" + "=" * 60)
    if all_ok:
        print("[OK] All required dependencies are installed correctly")
        return 0

    print("[FAIL] Missing required dependencies. Run: pip install -r requirements.txt")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
