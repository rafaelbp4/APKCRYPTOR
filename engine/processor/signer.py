import subprocess
import os
import shutil


KEYSTORE_PATH = "/tools/protect.keystore"
KEYSTORE_ALIAS = "protectkey"
KEYSTORE_PASS = "protect123"


def sign_apk(unsigned_apk: str, output_apk: str):
    """
    Sign APK using uber-apk-signer.
    Auto-generates a keystore if it doesn't exist.
    """
    # Generate keystore if not exists
    if not os.path.exists(KEYSTORE_PATH):
        _generate_keystore()

    # Align first
    aligned_apk = unsigned_apk.replace(".apk", "_aligned.apk")
    _zipalign(unsigned_apk, aligned_apk)

    # Sign with uber-apk-signer
    cmd = [
        "java", "-jar", "/tools/uber-apk-signer.jar",
        "--apks", aligned_apk,
        "--ks", KEYSTORE_PATH,
        "--ksAlias", KEYSTORE_ALIAS,
        "--ksPass", KEYSTORE_PASS,
        "--ksKeyPass", KEYSTORE_PASS,
        "--out", os.path.dirname(output_apk),
        "--allowResign",
        "--overwrite",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise Exception(f"Signing failed: {result.stderr}")

    # uber-apk-signer adds -aligned-signed suffix
    expected = aligned_apk.replace(".apk", "-aligned-signed.apk")
    if os.path.exists(expected):
        shutil.move(expected, output_apk)
    else:
        # Find signed file in output dir
        out_dir = os.path.dirname(output_apk)
        for f in os.listdir(out_dir):
            if "signed" in f and f.endswith(".apk"):
                shutil.move(os.path.join(out_dir, f), output_apk)
                break

    # Cleanup aligned
    if os.path.exists(aligned_apk):
        os.remove(aligned_apk)

    return output_apk


def _zipalign(input_apk: str, output_apk: str):
    """Zipalign for optimization"""
    cmd = ["zipalign", "-f", "-v", "4", input_apk, output_apk]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        # zipalign fail হলে original use করো
        shutil.copy(input_apk, output_apk)


def _generate_keystore():
    """Auto-generate a debug keystore"""
    os.makedirs(os.path.dirname(KEYSTORE_PATH), exist_ok=True)
    cmd = [
        "keytool", "-genkeypair",
        "-alias", KEYSTORE_ALIAS,
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "9125",
        "-keystore", KEYSTORE_PATH,
        "-storepass", KEYSTORE_PASS,
        "-keypass", KEYSTORE_PASS,
        "-dname", "CN=APKProtector, OU=Security, O=Protect, L=BD, S=BD, C=BD",
        "-noprompt"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise Exception(f"Keystore generation failed: {result.stderr}")
    print("[✓] Keystore generated")
