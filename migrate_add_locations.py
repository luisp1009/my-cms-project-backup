from db import user_sites_collection

# Default location
default_location = 'body'

# Find all user sites
all_sites = user_sites_collection.find()

for site in all_sites:
    username = site.get('username')
    fields = site.get('fields', [])
    updated = False

    for field in fields:
        if 'location' not in field:
            field['location'] = default_location
            updated = True

    if updated:
        user_sites_collection.update_one({'username': username}, {'$set': {'fields': fields}})
        print(f"Updated missing locations for user: {username}")

print("Migration complete. All fields now have locations.")
