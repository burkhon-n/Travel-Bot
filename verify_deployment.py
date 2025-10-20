#!/usr/bin/env python3
"""
Pre-deployment verification script.
Run this before pushing to Vercel to ensure everything is configured correctly.
"""

import sys
import os
from pathlib import Path

print("🔍 Vercel Deployment Pre-Check\n")
print("=" * 60)

errors = []
warnings = []
success = []

# Check 1: Verify api/index.py exists
print("\n✓ Checking api/index.py...")
if Path("api/index.py").exists():
    success.append("api/index.py exists")
    print("  ✅ Found")
else:
    errors.append("api/index.py not found")
    print("  ❌ Missing!")

# Check 2: Verify requirements.txt contains mangum
print("\n✓ Checking requirements.txt...")
if Path("requirements.txt").exists():
    with open("requirements.txt") as f:
        content = f.read()
        if "mangum" in content:
            success.append("mangum in requirements.txt")
            print("  ✅ mangum is listed")
        else:
            errors.append("mangum not in requirements.txt")
            print("  ❌ mangum is missing!")
else:
    errors.append("requirements.txt not found")
    print("  ❌ requirements.txt missing!")

# Check 3: Verify vercel.json points to api/index.py
print("\n✓ Checking vercel.json...")
if Path("vercel.json").exists():
    import json
    with open("vercel.json") as f:
        config = json.load(f)
        if config.get("builds", [{}])[0].get("src") == "api/index.py":
            success.append("vercel.json configured correctly")
            print("  ✅ Points to api/index.py")
        else:
            errors.append("vercel.json not pointing to api/index.py")
            print("  ❌ Wrong build source!")
else:
    errors.append("vercel.json not found")
    print("  ❌ vercel.json missing!")

# Check 4: Verify handler can be imported
print("\n✓ Testing handler import...")
try:
    sys.path.insert(0, str(Path.cwd()))
    from api.index import handler
    success.append("handler imports successfully")
    print(f"  ✅ Handler type: {type(handler).__name__}")
    print(f"  ✅ Handler is callable: {callable(handler)}")
except Exception as e:
    errors.append(f"handler import failed: {e}")
    print(f"  ❌ Import error: {e}")

# Check 5: Verify main.py has IS_VERCEL check
print("\n✓ Checking main.py for serverless support...")
if Path("main.py").exists():
    with open("main.py") as f:
        content = f.read()
        if "IS_VERCEL" in content:
            success.append("main.py has serverless detection")
            print("  ✅ Serverless environment detection enabled")
        else:
            warnings.append("main.py missing IS_VERCEL check")
            print("  ⚠️  No serverless detection (may cause issues)")
else:
    errors.append("main.py not found")
    print("  ❌ main.py missing!")

# Check 6: Verify runtime.txt exists
print("\n✓ Checking runtime.txt...")
if Path("runtime.txt").exists():
    with open("runtime.txt") as f:
        runtime = f.read().strip()
        success.append(f"runtime.txt specifies {runtime}")
        print(f"  ✅ Python version: {runtime}")
else:
    warnings.append("runtime.txt not found (Vercel will use default)")
    print("  ⚠️  Not found (will use default Python version)")

# Check 7: Verify .vercelignore exists
print("\n✓ Checking .vercelignore...")
if Path(".vercelignore").exists():
    success.append(".vercelignore exists")
    print("  ✅ Found")
else:
    warnings.append(".vercelignore not found")
    print("  ⚠️  Not found (may increase build size)")

# Summary
print("\n" + "=" * 60)
print("\n📊 SUMMARY:\n")

if success:
    print(f"✅ Success ({len(success)}):")
    for s in success:
        print(f"   • {s}")

if warnings:
    print(f"\n⚠️  Warnings ({len(warnings)}):")
    for w in warnings:
        print(f"   • {w}")

if errors:
    print(f"\n❌ Errors ({len(errors)}):")
    for e in errors:
        print(f"   • {e}")
    print("\n🚫 DEPLOYMENT NOT READY - Fix errors before deploying!")
    sys.exit(1)
else:
    print("\n✅ ALL CHECKS PASSED - Ready for deployment!")
    print("\nNext steps:")
    print("  1. git add .")
    print("  2. git commit -m 'Fix Vercel deployment with Mangum'")
    print("  3. git push origin main")
    print("  4. Watch Vercel build logs")
    sys.exit(0)
