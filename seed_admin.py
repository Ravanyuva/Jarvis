import database
from passlib.context import CryptContext

# Auth Config (Must match server.py)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_admin():
    print("Connecting to Database...")
    if not database.db.client:
        print("ERROR: Could not connect to MongoDB.")
        return

    admin_user = "admin"
    admin_pass = "admin"
    admin_email = "admin@123" # User requested this as email/identifier
    
    # Check if exists
    if database.db.get_user(admin_user):
        print(f"User '{admin_user}' already exists.")
        # Optional: Update password/subscription if needed, but for now just skip
    else:
        print(f"Creating user '{admin_user}'...")
        hashed_pwd = get_password_hash(admin_pass)
        success = database.db.create_user(admin_user, hashed_pwd, admin_email)
        
        if success:
            print(f"SUCCESS: User '{admin_user}' created.")
            # Promote to ULTRA plan
            database.db.update_subscription(admin_user, "ULTRA")
            print(f"SUCCESS: User '{admin_user}' upgraded to ULTRA.")
        else:
            print(f"FAILURE: Could not create user '{admin_user}'.")

if __name__ == "__main__":
    seed_admin()
