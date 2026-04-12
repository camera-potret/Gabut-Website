import os
from pymongo import MongoClient
from bson.objectid import ObjectId

DATABASE_URL = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/')

client = MongoClient(DATABASE_URL)
# Get the default database (from conn string) or default to gabut_db
db = client.get_default_database(default='gabut_db')

def init_db():
    if db.settings.count_documents({}) == 0:
        db.settings.insert_one({
            'profile_name': 'Camrta_potret_',
            'profile_picture': '',
            'background_picture': '',
            'tiktok_url': '',
            'instagram_url': '',
            'facebook_url': ''
        })

def get_settings():
    settings = db.settings.find_one({})
    if settings:
        settings['id'] = str(settings.pop('_id'))
    return settings

def update_settings(profile_name=None, profile_picture=None, background_picture=None, tiktok_url=None, instagram_url=None, facebook_url=None):
    update_data = {}
    if profile_name is not None: update_data['profile_name'] = profile_name
    if profile_picture is not None: update_data['profile_picture'] = profile_picture
    if background_picture is not None: update_data['background_picture'] = background_picture
    if tiktok_url is not None: update_data['tiktok_url'] = tiktok_url
    if instagram_url is not None: update_data['instagram_url'] = instagram_url
    if facebook_url is not None: update_data['facebook_url'] = facebook_url
    
    if update_data:
        settings = db.settings.find_one({})
        if settings:
            db.settings.update_one({'_id': settings['_id']}, {'$set': update_data})

def get_links():
    links = list(db.links.find().sort([('order_num', 1), ('_id', -1)]))
    for link in links:
        link['id'] = str(link.pop('_id'))
    return links

def add_link(title, url):
    db.links.insert_one({
        'title': title,
        'url': url,
        'order_num': 0
    })

def delete_link(link_id):
    try:
        db.links.delete_one({'_id': ObjectId(link_id)})
    except Exception:
        pass

def update_link(link_id, title, url):
    try:
        db.links.update_one({'_id': ObjectId(link_id)}, {'$set': {'title': title, 'url': url}})
    except Exception:
        pass

def update_links_order(order_list):
    for index, link_id in enumerate(order_list):
        try:
            db.links.update_one({'_id': ObjectId(link_id)}, {'$set': {'order_num': index}})
        except Exception:
            pass

if __name__ == '__main__':
    init_db()
