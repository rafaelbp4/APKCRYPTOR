import subprocess
import os


def decompile_apk(apk_path: str, output_dir: str):
    """Decompile APK using apktool"""
    cmd = [
        "java", "-jar", "/tools/apktool.jar",
        "d", apk_path,
        "-o", output_dir,
        "-f",  # force overwrite
        "--no-src",  # keep smali, don't convert to java
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise Exception(f"Decompile failed: {result.stderr}")
    return output_dir


def recompile_apk(decompiled_dir: str, output_apk: str):
    """Recompile decompiled APK using apktool"""
    cmd = [
        "java", "-jar", "/tools/apktool.jar",
        "b", decompiled_dir,
        "-o", output_apk,
        "--use-aapt2",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        # Try without aapt2 if fails
        cmd.remove("--use-aapt2")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            raise Exception(f"Recompile failed: {result.stderr}")
    return output_apk
