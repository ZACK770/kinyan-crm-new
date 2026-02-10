"""
Helper script to add Nedarim Plus credentials to .env file
"""
import os

ENV_FILE = ".env"
BACKUP_FILE = ".env.backup"

# Nedarim Plus credentials
NEDARIM_CONFIG = """
# ── Nedarim Plus Payment Gateway ─────────────────────────
NEDARIM_API_URL=https://api.nedarimplus.co.il/v1
NEDARIM_API_KEY=ou946
NEDARIM_MOSAD_ID=7009959
NEDARIM_WEBHOOK_SECRET=change-this-to-webhook-secret
"""

def add_nedarim_to_env():
    """Add Nedarim Plus configuration to .env file"""
    
    # Check if .env exists
    if not os.path.exists(ENV_FILE):
        print(f"❌ File {ENV_FILE} not found!")
        print(f"💡 Creating {ENV_FILE} from .env.example...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r", encoding="utf-8") as f:
                content = f.read()
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Created {ENV_FILE}")
        else:
            print("❌ .env.example not found either!")
            return
    
    # Read current .env
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if Nedarim config already exists
    if "NEDARIM_API_KEY" in content:
        print("⚠️  Nedarim Plus configuration already exists in .env")
        print("Current values:")
        for line in content.split("\n"):
            if line.startswith("NEDARIM_"):
                print(f"  {line}")
        
        response = input("\n❓ Do you want to update? (y/n): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Backup current .env
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Backed up to {BACKUP_FILE}")
        
        # Remove old Nedarim config
        lines = content.split("\n")
        new_lines = []
        skip_until_blank = False
        
        for line in lines:
            if "Nedarim Plus Payment Gateway" in line:
                skip_until_blank = True
                continue
            if skip_until_blank:
                if line.strip() == "" or line.startswith("#") and "──" not in line:
                    skip_until_blank = False
                    new_lines.append(line)
                continue
            if not line.startswith("NEDARIM_"):
                new_lines.append(line)
        
        content = "\n".join(new_lines)
    
    # Add Nedarim config
    if not content.endswith("\n\n"):
        content += "\n"
    content += NEDARIM_CONFIG
    
    # Write back
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("✅ Nedarim Plus configuration added to .env!")
    print("="*60)
    print("\nAdded configuration:")
    print(NEDARIM_CONFIG)
    print("\n" + "="*60)
    print("📝 Next steps:")
    print("="*60)
    print("1. Review the .env file")
    print("2. Update NEDARIM_WEBHOOK_SECRET if you have it")
    print("3. Restart your server: python app.py")
    print("="*60)

if __name__ == "__main__":
    add_nedarim_to_env()
