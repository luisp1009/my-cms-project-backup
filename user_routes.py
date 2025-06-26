import os
from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from db import users_collection, user_sites_collection

user_bp = Blueprint('user', __name__)

UPLOAD_FOLDER = 'static/uploads'

@user_bp.route('/user-register', methods=['GET', 'POST'])
def user_register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        slug = request.form['slug']

        existing_user = users_collection.find_one({'username': username})
        existing_slug = users_collection.find_one({'slug': slug})

        if existing_user:
            error = 'Username already exists.'
        elif existing_slug:
            error = 'This slug is already taken. Please choose another one.'
        else:
            users_collection.insert_one({
                'username': username,
                'password': password,
                'slug': slug
            })
            user_sites_collection.insert_one({
                'username': username,
                'layout': 'layout1',
                'fields': []
            })
            return redirect('/user-login')

    return render_template('user_register.html', error=error)

@user_bp.route('/user-login', methods=['GET', 'POST'])
def user_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({'username': username})

        if user and password == user['password']:
            session['user_logged_in'] = True
            session['username'] = username
            return redirect('/user-dashboard')
        else:
            error = 'Invalid username or password.'

    return render_template('user_login.html', error=error)

@user_bp.route('/user-dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if not session.get('user_logged_in'):
        return redirect('/user-login')

    username = session.get('username')
    user_site = user_sites_collection.find_one({'username': username})

    return render_template('user_dashboard.html', content=user_site, username=username, slug=username)

@user_bp.route('/user-update-content/<username>', methods=['POST'])
def user_update_content(username):
    if not session.get('user_logged_in'):
        return redirect('/user-login')

    user_site = user_sites_collection.find_one({'username': username})

    if not user_site:
        return 'User site not found', 404

    fields = user_site.get('fields', [])
    updates = {}

    for field in fields:
        field_name = field['name']

        if field['type'] == 'text':
            updates[field_name] = request.form.get(field_name, '')

        elif field['type'] == 'multiimage':
            files = request.files.getlist(field_name)
            image_paths = []

            for file in files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    image_paths.append('/' + filepath)

            if image_paths:
                updates[field_name] = image_paths
            else:
                updates[field_name] = user_site.get(field_name, [])

    user_sites_collection.update_one({'username': username}, {'$set': updates})

    return redirect('/user-dashboard')

@user_bp.route('/user-remove-field/<username>/<field_name>', methods=['POST'])
def user_remove_field(username, field_name):
    if not session.get('user_logged_in'):
        return redirect('/user-login')

    user_site = user_sites_collection.find_one({'username': username})

    if user_site:
        updated_fields = [field for field in user_site.get('fields', []) if field['name'] != field_name]
        user_sites_collection.update_one({'username': username}, {'$set': {'fields': updated_fields}})
        user_sites_collection.update_one({'username': username}, {'$unset': {field_name: ""}})

    return redirect('/user-dashboard')

@user_bp.route('/user-logout')
def user_logout():
    session.pop('user_logged_in', None)
    return redirect('/user-login')
