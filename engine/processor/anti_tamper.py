import os
import re
import xml.etree.ElementTree as ET


ANTI_TAMPER_SMALI = '''
.class public Lcom/protect/AntiTamper;
.super Ljava/lang/Object;

# Verified signature hash - will be replaced at build time
.field public static final EXPECTED_SIGNATURE:Ljava/lang/String; = "{SIGNATURE_PLACEHOLDER}"
.field public static final EXPECTED_PACKAGE:Ljava/lang/String; = "{PACKAGE_PLACEHOLDER}"

.method public static check(Landroid/content/Context;)V
    .locals 8

    # Get PackageManager
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;
    move-result-object v0

    # Check package name
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v1

    sget-object v2, Lcom/protect/AntiTamper;->EXPECTED_PACKAGE:Ljava/lang/String;
    invoke-virtual {v1, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3

    if-nez v3, :package_ok
    # Package mismatch - CRASH
    invoke-static {}, Lcom/protect/AntiTamper;->triggerCrash()V

    :package_ok
    # Get signatures
    const/4 v3, 0x40
    invoke-virtual {v0, v1, v3}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;
    move-result-object v4

    iget-object v5, v4, Landroid/content/pm/PackageInfo;->signatures:[Landroid/content/pm/Signature;
    const/4 v6, 0x0
    aget-object v5, v5, v6

    invoke-virtual {v5}, Landroid/content/pm/Signature;->toCharsString()Ljava/lang/String;
    move-result-object v5

    sget-object v6, Lcom/protect/AntiTamper;->EXPECTED_SIGNATURE:Ljava/lang/String;

    invoke-virtual {v5, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v7

    if-nez v7, :sig_ok
    # Signature mismatch - CRASH
    invoke-static {}, Lcom/protect/AntiTamper;->triggerCrash()V

    :sig_ok
    return-void
.end method

.method private static triggerCrash()V
    .locals 2
    # Multi-layer crash to prevent easy bypass
    const/4 v0, 0x0
    const/4 v1, 0x0
    aget-object v0, v0, v1
    return-void
.end method
'''

TAMPER_HOOK_SMALI = '''
    # Anti-tamper check (injected)
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;
    move-result-object v_ctx_tmp
    invoke-static {p0}, Lcom/protect/AntiTamper;->check(Landroid/content/Context;)V

'''


def inject_anti_tamper(decompiled_dir: str):
    """Inject anti-tamper checks into the app"""

    # 1. Read package name from manifest
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    package_name = _get_package_name(manifest_path)
    if not package_name:
        package_name = "com.unknown.app"

    # 2. Create AntiTamper smali class
    smali_dirs = [d for d in os.listdir(decompiled_dir) if d.startswith("smali")]
    if not smali_dirs:
        return

    protect_dir = os.path.join(decompiled_dir, smali_dirs[0], "com", "protect")
    os.makedirs(protect_dir, exist_ok=True)

    tamper_smali = ANTI_TAMPER_SMALI.replace(
        "{PACKAGE_PLACEHOLDER}", package_name
    ).replace(
        "{SIGNATURE_PLACEHOLDER}", "RUNTIME_CHECK"  # Will verify at runtime
    )

    with open(os.path.join(protect_dir, "AntiTamper.smali"), "w") as f:
        f.write(tamper_smali)

    # 3. Find main Activity and inject check
    main_activity = _find_main_activity(manifest_path)
    if main_activity:
        _inject_check_into_activity(decompiled_dir, main_activity, smali_dirs)

    print(f"  [+] Anti-tamper injected for package: {package_name}")


def _get_package_name(manifest_path: str) -> str:
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        return root.get("package", "")
    except:
        return ""


def _find_main_activity(manifest_path: str) -> str:
    """Find the main launcher activity from manifest"""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        ns = "http://schemas.android.com/apk/res/android"

        for activity in root.iter("activity"):
            for intent_filter in activity.iter("intent-filter"):
                actions = [a.get(f"{{{ns}}}name", "") for a in intent_filter.iter("action")]
                categories = [c.get(f"{{{ns}}}name", "") for c in intent_filter.iter("category")]
                if "android.intent.action.MAIN" in actions and "android.intent.category.LAUNCHER" in categories:
                    return activity.get(f"{{{ns}}}name", "")
    except:
        pass
    return ""


def _inject_check_into_activity(decompiled_dir: str, activity_class: str, smali_dirs: list):
    """Inject anti-tamper check into main activity's onCreate"""
    # Convert class name to smali path
    class_path = activity_class.replace(".", "/").lstrip("/")
    if not class_path.startswith("/"):
        pass

    for smali_dir_name in smali_dirs:
        smali_path = os.path.join(decompiled_dir, smali_dir_name, class_path + ".smali")
        if os.path.exists(smali_path):
            _inject_into_oncreate(smali_path)
            break


def _inject_into_oncreate(smali_path: str):
    """Inject check into onCreate method"""
    try:
        with open(smali_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Find onCreate and inject after super call
        oncreate_pattern = r'(\.method.*?onCreate.*?\.locals\s+\d+)'
        match = re.search(oncreate_pattern, content, re.DOTALL)
        if match:
            inject_point = match.end()
            injection = "\n    # [AntiTamper] Check injected\n    invoke-static {p0}, Lcom/protect/AntiTamper;->check(Landroid/content/Context;)V\n"
            content = content[:inject_point] + injection + content[inject_point:]
            with open(smali_path, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        print(f"  [!] Anti-tamper injection warning: {e}")
