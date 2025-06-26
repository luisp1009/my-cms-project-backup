from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb+srv://luisparedes1009:Ironroof113@cluster0.dvva0do.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['cms_database']

users_collection = db['users']
user_sites_collection = db['user_sites']
admins_collection = db['admins']
