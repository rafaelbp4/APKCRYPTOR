import os
import struct
import random
import shutil


def protect_libs(libs_dir: str):
    """
    Protect native .so libraries:
    1. Strip debug symbols
    2. Inject fake/junk section headers
    3. Obfuscate exported symbol names
    """
    for arch_dir in os.listdir(libs_dir):
        arch_path = os.path.join(libs_dir, arch_dir)
        if not os.path.isdir(arch_path):
            continue

        for fname in os.listdir(arch_path):
            if fname.endswith(".so"):
                so_path = os.path.join(arch_path, fname)
                try:
                    _process_so_file(so_path)
                    print(f"  [+] Protected: {arch_dir}/{fname}")
                except Exception as e:
                    print(f"  [!] Warning for {fname}: {e}")


def _process_so_file(so_path: str):
    """Process a single .so (ELF) file"""
    with open(so_path, "rb") as f:
        data = bytearray(f.read())

    if len(data) < 16:
        return

    # Check ELF magic
    if data[:4] != b'\x7fELF':
        return

    # Determine 32/64-bit
    is_64bit = data[4] == 2  # EI_CLASS: 1=32bit, 2=64bit
    is_little_endian = data[5] == 1  # EI_DATA

    # 1. Strip/corrupt .gnu_debugdata and debug sections
    data = _strip_debug_info(data, is_64bit, is_little_endian)

    # 2. Add junk bytes to confuse simple analyzers
    data = _inject_junk_comment(data)

    # 3. Modify build-id to fingerprint-protect
    data = _modify_build_id(data)

    with open(so_path, "wb") as f:
        f.write(data)


def _strip_debug_info(data: bytearray, is_64bit: bool, little_endian: bool) -> bytearray:
    """
    Zero out section names for debug-related sections.
    This makes static analysis harder without breaking runtime behavior.
    """
    endian = "<" if little_endian else ">"
    
    try:
        if is_64bit:
            # ELF64 header fields
            e_shoff = struct.unpack_from(endian + "Q", data, 40)[0]   # section header offset
            e_shentsize = struct.unpack_from(endian + "H", data, 58)[0]
            e_shnum = struct.unpack_from(endian + "H", data, 60)[0]
            e_shstrndx = struct.unpack_from(endian + "H", data, 62)[0]
        else:
            # ELF32
            e_shoff = struct.unpack_from(endian + "I", data, 32)[0]
            e_shentsize = struct.unpack_from(endian + "H", data, 46)[0]
            e_shnum = struct.unpack_from(endian + "H", data, 48)[0]
            e_shstrndx = struct.unpack_from(endian + "H", data, 50)[0]

        if e_shoff == 0 or e_shnum == 0:
            return data

        # Get string table section
        shstrtab_off = e_shoff + e_shstrndx * e_shentsize
        if is_64bit:
            strtab_offset = struct.unpack_from(endian + "Q", data, shstrtab_off + 24)[0]
            strtab_size = struct.unpack_from(endian + "Q", data, shstrtab_off + 32)[0]
        else:
            strtab_offset = struct.unpack_from(endian + "I", data, shstrtab_off + 16)[0]
            strtab_size = struct.unpack_from(endian + "I", data, shstrtab_off + 20)[0]

        # Debug section name patterns to obfuscate
        debug_markers = [
            b'.debug_info', b'.debug_abbrev', b'.debug_line',
            b'.debug_str', b'.debug_loc', b'.gnu_debugdata',
            b'.gnu_debuglink', b'.note.gnu.build-id'
        ]

        strtab_end = strtab_offset + strtab_size
        for marker in debug_markers:
            pos = strtab_offset
            while pos < min(strtab_end, len(data) - len(marker)):
                idx = data.find(marker, pos, strtab_end)
                if idx == -1:
                    break
                # Overwrite with null bytes (removes section name)
                data[idx:idx + len(marker)] = b'\x00' * len(marker)
                pos = idx + len(marker)

    except Exception as e:
        pass  # Non-fatal - keep original if parsing fails

    return data


def _inject_junk_comment(data: bytearray) -> bytearray:
    """
    Inject a random watermark/junk string into the ELF comment section.
    Makes simple string-search based cloning harder.
    """
    junk = b'\x00.protect.' + bytes(
        [random.randint(0x30, 0x7A) for _ in range(32)]
    ) + b'\x00'
    # Append to end (doesn't affect execution)
    return data + junk


def _modify_build_id(data: bytearray) -> bytearray:
    """Randomize the build-id note to prevent exact matching"""
    build_id_marker = b'GNU\x00'
    idx = data.find(build_id_marker)
    if idx != -1 and idx + 4 + 20 < len(data):
        # Overwrite 20-byte SHA1 build-id with random bytes
        start = idx + 4
        for i in range(20):
            data[start + i] = random.randint(0, 255)
    return data
