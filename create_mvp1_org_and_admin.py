import asyncio
from mvp1_auth import MVP1AuthService
from mvp1_models import MVP1Organization
from database import DatabaseOperations

async def main():
    # Define organization details
    org_data = {
        "name": "Daakyi MVP1 Org",
        "industry": "Compliance Technology",
        "size": "Small (1-50)",
        "headquarters_location": "Global",
        "supported_frameworks": ["ISO 27001", "NIST CSF", "SOC 2 Type I"]
    }

    # Check if organization already exists
    existing_org = await DatabaseOperations.find_one("mvp1_organizations", {"name": org_data["name"]})
    if existing_org:
        org_id = existing_org["id"]
        print(f"Organization already exists: {org_data['name']} (ID: {org_id})")
    else:
        new_org = MVP1Organization(**org_data)
        await DatabaseOperations.insert_one("mvp1_organizations", new_org.dict())
        org_id = new_org.id
        print(f"Created organization: {org_data['name']} (ID: {org_id})")

    # Create initial admin user for this organization
    admin_user = await MVP1AuthService.setup_initial_admin(org_id)
    print(f"Admin user created: {admin_user.email}")
    print(f"Name: {admin_user.name}")
    print(f"Role: {admin_user.role}")
    print(f"Organization ID: {admin_user.organization_id}")
    print("Default password: DaakyiSecure2025!")

if __name__ == "__main__":
    asyncio.run(main())
