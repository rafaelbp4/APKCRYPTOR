import os
import re
import random
import string
import xml.etree.ElementTree as ET


def obfuscate_resources(decompiled_dir: str):
    """
    Obfuscate resource names in res/ folder and update references.
    Renames drawable, layout, string resource IDs.
    """
    res_dir = os.path.join(decompiled_dir, "res")
    if not os.path.exists(res_dir):
        return

    # Build mapping of old name → new name
    name_map = {}
    _build_resource_map(res_dir, name_map)

    if not name_map:
        return

    # Apply renaming to XML files
    _apply_renaming(decompiled_dir, name_map)
    print(f"  [+] Obfuscated {len(name_map)} resource names")


def _build_resource_map(res_dir: str, name_map: dict):
    """Create obfuscated names for each resource file"""
    used_names = set()

    for folder in os.listdir(res_dir):
        folder_path = os.path.join(res_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        # Only obfuscate drawable and layout names
        folder_base = folder.split("-")[0]
        if folder_base not in ("drawable", "layout", "anim", "menu"):
            continue

        for fname in os.listdir(folder_path):
            if "." not in fname:
                continue
            name, ext = fname.rsplit(".", 1)
            if name not in name_map:
                new_name = _gen_obf_name(used_names)
                used_names.add(new_name)
                name_map[name] = new_name

            # Rename the file
            old_path = os.path.join(folder_path, fname)
            new_path = os.path.join(folder_path, f"{name_map[name]}.{ext}")
            try:
                os.rename(old_path, new_path)
            except Exception:
                pass


def _apply_renaming(decompiled_dir: str, name_map: dict):
    """Update all XML and smali references to renamed resources"""
    # Process XML files in res/
    res_dir = os.path.join(decompiled_dir, "res")
    for root, dirs, files in os.walk(res_dir):
        for fname in files:
            if fname.endswith(".xml"):
                _replace_in_file(os.path.join(root, fname), name_map)

    # Process smali files
    for d in os.listdir(decompiled_dir):
        if d.startswith("smali"):
            smali_dir = os.path.join(decompiled_dir, d)
            for root, dirs, files in os.walk(smali_dir):
                for fname in files:
                    if fname.endswith(".smali"):
                        _replace_in_file(os.path.join(root, fname), name_map)

    # Process AndroidManifest.xml
    manifest = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if os.path.exists(manifest):
        _replace_in_file(manifest, name_map)


def _replace_in_file(filepath: str, name_map: dict):
    """Replace all resource name occurrences in a file"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        original = content
        for old_name, new_name in name_map.items():
            # Replace in XML: @drawable/name, @layout/name, etc.
            content = content.replace(f"/{old_name}", f"/{new_name}")
            content = content.replace(f'"{old_name}"', f'"{new_name}"')

        if content != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception:
        pass


def _gen_obf_name(used: set) -> str:
    """Generate a random short name like a, b, aa, ab..."""
    chars = string.ascii_lowercase
    # Start with 2-char names to avoid conflicts
    for length in [2, 3, 4]:
        for _ in range(200):
            name = "r" + "".join(random.choices(chars, k=length))
            if name not in used:
                return name
    return "r" + "".join(random.choices(chars, k=8))
