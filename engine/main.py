from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import tempfile
import os
import json
import shutil
import uuid

from processor.decompiler import decompile_apk, recompile_apk
from processor.string_encryptor import encrypt_strings
from processor.anti_tamper import inject_anti_tamper
from processor.libs_protector import protect_libs
from processor.resource_obfuscator import obfuscate_resources
from processor.signer import sign_apk

app = FastAPI(title="APK Protector Engine", version="1.0.0")

@app.get("/")
def root():
    return {"status": "APK Protector Engine running ✅"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/protect")
async def protect_apk(
    file: UploadFile = File(...),
    options: str = Form(default="{}")
):
    work_dir = tempfile.mkdtemp(prefix="apk_protect_")
    
    try:
        opts = json.loads(options)
        
        # 1. Save uploaded APK
        apk_path = os.path.join(work_dir, "input.apk")
        with open(apk_path, "wb") as f:
            f.write(await file.read())
        
        print(f"[*] APK saved: {apk_path}")
        
        # 2. Decompile APK
        decompiled_dir = os.path.join(work_dir, "decompiled")
        decompile_apk(apk_path, decompiled_dir)
        print("[✓] Decompilation complete")
        
        # 3. String Encryption
        if opts.get("string_encryption", True):
            encrypt_strings(decompiled_dir)
            print("[✓] String encryption complete")
        
        # 4. Anti-Tamper Injection
        if opts.get("anti_tamper", True):
            inject_anti_tamper(decompiled_dir)
            print("[✓] Anti-tamper injected")
        
        # 5. Libs Protection (.so files)
        if opts.get("libs_protection", True):
            libs_dir = os.path.join(decompiled_dir, "lib")
            if os.path.exists(libs_dir):
                protect_libs(libs_dir)
                print("[✓] Libs protection complete")
            else:
                print("[!] No libs folder found, skipping")
        
        # 6. Resource Obfuscation
        if opts.get("resource_obfuscation", True):
            obfuscate_resources(decompiled_dir)
            print("[✓] Resource obfuscation complete")
        
        # 7. Recompile APK
        unsigned_apk = os.path.join(work_dir, "unsigned.apk")
        recompile_apk(decompiled_dir, unsigned_apk)
        print("[✓] Recompilation complete")
        
        # 8. Sign APK
        signed_apk = os.path.join(work_dir, "protected_signed.apk")
        sign_apk(unsigned_apk, signed_apk)
        print("[✓] APK signed")
        
        # 9. Return protected APK
        output_name = file.filename.replace(".apk", "_protected.apk")
        return FileResponse(
            signed_apk,
            media_type="application/vnd.android.package-archive",
            filename=output_name,
            background=None
        )
    
    except Exception as e:
        print(f"[✗] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
    finally:
        # Cleanup temp dir after response sent
        def cleanup():
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

@app.get("/ping")
def ping():
    """cron-job.org এই endpoint ping করবে 24/7 জাগিয়ে রাখতে"""
    return {"status": "ok", "message": "pong", "service": "apk-engine"}
