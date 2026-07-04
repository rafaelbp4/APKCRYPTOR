import os
import re
import base64
import random
import string


# Decryptor smali code that gets injected into the app
DECRYPTOR_SMALI = '''
.class public Lcom/protect/StringDecryptor;
.super Ljava/lang/Object;

.method public static decrypt(Ljava/lang/String;)Ljava/lang/String;
    .locals 3

    # Decode base64
    invoke-static {p0}, Landroid/util/Base64;->decode(Ljava/lang/String;I)[B
    move-result-object v0

    # XOR decode
    new-array v1, v0, [B
    const/4 v2, 0x0
    array-length v3, v0

    :loop_start
    if-ge v2, v3, :loop_end
    aget-byte v4, v0, v2
    xor-int/lit8 v4, v4, 0x{XOR_KEY}
    aput-byte v4, v1, v2
    add-int/lit8 v2, v2, 0x1
    goto :loop_start

    :loop_end
    new-instance v0, Ljava/lang/String;
    invoke-direct {{v0, v1}}, Ljava/lang/String;-><init>([B)V
    return-object v0
.end method
'''

def _xor_encrypt(text: str, key: int) -> str:
    """XOR encrypt string and return base64"""
    encrypted = bytes([b ^ key for b in text.encode("utf-8")])
    return base64.b64encode(encrypted).decode("utf-8")


def _generate_xor_key() -> int:
    return random.randint(0x20, 0x7F)


def encrypt_strings(decompiled_dir: str):
    """Find all string constants in smali and encrypt them"""
    smali_dirs = []
    for d in os.listdir(decompiled_dir):
        if d.startswith("smali"):
            smali_dirs.append(os.path.join(decompiled_dir, d))

    if not smali_dirs:
        return

    xor_key = _generate_xor_key()

    # Inject decryptor class
    protect_dir = os.path.join(smali_dirs[0], "com", "protect")
    os.makedirs(protect_dir, exist_ok=True)
    decryptor_path = os.path.join(protect_dir, "StringDecryptor.smali")
    with open(decryptor_path, "w") as f:
        f.write(DECRYPTOR_SMALI.replace("{XOR_KEY}", format(xor_key, '02x')))

    # Process all smali files
    for smali_dir in smali_dirs:
        for root, dirs, files in os.walk(smali_dir):
            # Skip our own protector classes
            if "com/protect" in root:
                continue
            for fname in files:
                if fname.endswith(".smali"):
                    fpath = os.path.join(root, fname)
                    _encrypt_strings_in_file(fpath, xor_key)


def _encrypt_strings_in_file(filepath: str, xor_key: int):
    """Encrypt string constants in a single smali file"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Match: const-string vX, "some string"
        pattern = r'(const-string(?:/jumbo)?\s+\w+,\s+)"([^"]{4,})"'
        
        def replace_string(match):
            prefix = match.group(1)
            original = match.group(2)
            
            # Skip empty, system-like strings
            if _should_skip_string(original):
                return match.group(0)
            
            encrypted = _xor_encrypt(original, xor_key)
            reg = match.group(0).split(",")[0].split()[-1]  # get register name
            
            # Replace with decrypt call
            return (
                f'const-string {reg}, "{encrypted}"\n'
                f'    invoke-static {{{reg}}}, Lcom/protect/StringDecryptor;->decrypt(Ljava/lang/String;)Ljava/lang/String;\n'
                f'    move-result-object {reg}'
            )
        
        new_content = re.sub(pattern, replace_string, content)
        
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
    except Exception as e:
        print(f"  [!] String encryption warning for {filepath}: {e}")


def _should_skip_string(s: str) -> bool:
    """Skip strings that shouldn't be encrypted"""
    skip_patterns = [
        r'^[A-Z_]+$',               # Constants like LOG_TAG
        r'^(true|false|null)$',     # Literals
        r'^\d+(\.\d+)?$',           # Numbers
        r'^[./\\]',                  # Paths
        r'android\.',               # Android classes
        r'java\.',                  # Java classes
        r'^(GET|POST|PUT|DELETE)$', # HTTP methods
        r'^\s*$',                   # Whitespace
    ]
    for pat in skip_patterns:
        if re.search(pat, s, re.IGNORECASE):
            return True
    return len(s) < 4
