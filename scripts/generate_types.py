"""
Generate TypeScript types from FastAPI OpenAPI schema.

This script:
1. Runs the FastAPI app temporarily
2. Fetches the OpenAPI JSON schema
3. Converts it to TypeScript types
4. Saves to frontend/src/types/api.generated.ts

Usage:
    python scripts/generate_types.py

Requirements:
    npm install -D openapi-typescript (in frontend/)
"""
import subprocess
import sys
import json
import os
from pathlib import Path


def main():
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    
    # Check if openapi-typescript is installed
    node_modules = frontend_dir / "node_modules" / "openapi-typescript"
    
    if not node_modules.exists():
        print("📦 Installing openapi-typescript...")
        subprocess.run(
            ["npm", "install", "-D", "openapi-typescript"],
            cwd=frontend_dir,
            check=True,
            shell=True,  # Required for Windows
        )
    
    # Export OpenAPI schema directly (without running server)
    print("📝 Generating OpenAPI schema...")
    
    # Add project root to path
    sys.path.insert(0, str(project_root))
    
    # Set required environment variables
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test.db")
    os.environ.setdefault("SECRET_KEY", "test")
    os.environ.setdefault("JWT_SECRET_KEY", "test")
    
    from app import app
    
    # Get OpenAPI schema
    openapi_schema = app.openapi()
    
    # Save to temp file
    schema_path = project_root / "openapi.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"✅ OpenAPI schema saved to {schema_path}")
    
    # Generate TypeScript types
    output_path = frontend_dir / "src" / "types" / "api.generated.ts"
    print(f"🔧 Generating TypeScript types...")
    
    # Use shell=True for Windows compatibility with npx
    result = subprocess.run(
        f'npx openapi-typescript "{schema_path}" -o "{output_path}"',
        cwd=frontend_dir,
        capture_output=True,
        text=True,
        shell=True,  # Required for Windows
    )
    
    if result.returncode != 0:
        print(f"❌ Error generating types: {result.stderr}")
        # Try alternative approach using node directly
        print("🔄 Trying alternative method...")
        result = subprocess.run(
            f'node node_modules/openapi-typescript/bin/cli.js "{schema_path}" -o "{output_path}"',
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            shell=True,
        )
        if result.returncode != 0:
            print(f"❌ Alternative also failed: {result.stderr}")
            sys.exit(1)
    
    print(f"✅ TypeScript types generated at {output_path}")
    
    # Clean up
    schema_path.unlink()
    print("🧹 Cleaned up temporary files")
    
    print("\n📋 Next steps:")
    print("   1. Import types from '@/types/api.generated'")
    print("   2. Run this script whenever you change API schemas")
    print("   3. Add to package.json: \"types:sync\": \"python ../scripts/generate_types.py\"")


if __name__ == "__main__":
    main()
