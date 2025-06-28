import os
from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from db import users_collection, user_sites_collection

user_bp = Blueprint('user', __name__)

# Correct absolute upload path
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../frontend/static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists


@user_bp.route('/user-register', methods=['GET', 'POST'])
def user_register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        slug = request.form['slug']

        existing_user = users_collection.find_one({'username': username})

        if existing_user:
            error = 'User already exists.'
        else:
            users_collection.insert_one({'username': username, 'password': password})
            user_sites_collection.insert_one({
                'username': username,
                'slug': slug,
                'layout': 'layout1',
                'sections': ['nav', 'hero', 'body', 'footer'],
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
            session['user'] = username
            return redirect(f'/user-dashboard/{username}')
        else:
            error = 'Invalid user credentials.'

    return render_template('user_login.html', error=error)


@user_bp.route('/user-dashboard/<username>')
def user_dashboard(username):
    if session.get('user') != username:
        return redirect('/user-login')

    user_site = user_sites_collection.find_one({'username': username})

    if not user_site:
        return 'User site not found', 404

    return render_template('user_dashboard.html', username=username, content=user_site, slug=user_site.get('slug'))


@user_bp.route('/user-update-content/<username>', methods=['POST'])
def user_update_content(username):
    if session.get('user') != username:
        return redirect('/user-login')

    user_site = user_sites_collection.find_one({'username': username})
    updates = {}

    for field in user_site.get('fields', []):
        field_name = field['name']

        if field['type'] == 'text':
            updates[field_name] = request.form.get(field_name, '')

        elif field['type'] == 'multiimage':
            files = request.files.getlist(field_name)
            new_file_paths = []

            for img in files:
                if img.filename != '':
                    filename = secure_filename(img.filename)
                    img.save(os.path.join(UPLOAD_FOLDER, filename))
                    new_file_paths.append(f'/static/uploads/{filename}')

            if new_file_paths:
                updates[field_name] = new_file_paths
            else:
                updates[field_name] = user_site.get(field_name, [])

    if updates:
        user_sites_collection.update_one({'username': username}, {'$set': updates})
        print(f"Content updated for {username}: {updates}")
    else:
        print("No updates found.")

    return redirect(f'/user-dashboard/{username}')


@user_bp.route('/user-remove-field/<username>/<field_name>', methods=['POST'])
def user_remove_field(username, field_name):
    if session.get('user') != username:
        return redirect('/user-login')

    user_site = user_sites_collection.find_one({'username': username})

    if user_site:
        updated_fields = [field for field in user_site.get('fields', []) if field['name'] != field_name]
        user_sites_collection.update_one({'username': username}, {'$set': {'fields': updated_fields}})
        user_sites_collection.update_one({'username': username}, {'$unset': {field_name: ""}})

    return redirect(f'/user-dashboard/{username}')


@user_bp.route('/user-logout')
def user_logout():
    session.pop('user', None)
    return redirect('/user-login')
