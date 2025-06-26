import os
import time
from flask import Blueprint, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from db import users_collection, user_sites_collection, admins_collection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = admins_collection.find_one({'username': username})
        if admin and password == admin['password']:
            session['super_admin'] = True
            return redirect('/admin-dashboard')
        else:
            error = 'Invalid admin credentials.'

    return render_template('admin_login.html', error=error)

@admin_bp.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('super_admin'):
        return redirect('/admin-login')

    all_users = list(users_collection.find())
    return render_template('admin_dashboard_select.html', users=all_users)

@admin_bp.route('/admin-manage/<username>')
def admin_manage(username):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    user_site = user_sites_collection.find_one({'username': username})
    if not user_site:
        return 'User site not found', 404

    layout_folder = os.path.join('templates', 'layouts')
    available_layouts = [f.replace('.html', '') for f in os.listdir(layout_folder) if f.endswith('.html')]

    return render_template('admin_manage.html', content=user_site, username=username, layouts=available_layouts)

@admin_bp.route('/admin-update-layout/<username>', methods=['POST'])
def update_layout(username):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    layout = request.form.get('layout', 'layout1')
    user_sites_collection.update_one({'username': username}, {'$set': {'layout': layout}})
    return redirect(f'/admin-manage/{username}')

@admin_bp.route('/admin-add-field/<username>', methods=['POST'])
def add_field(username):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    new_field_name = request.form['new_field_name']
    new_field_type = request.form['new_field_type']

    user_site = user_sites_collection.find_one({'username': username})
    fields = user_site.get('fields', [])

    if not any(field['name'] == new_field_name for field in fields):
        fields.append({'name': new_field_name, 'type': new_field_type})
        user_sites_collection.update_one({'username': username}, {'$set': {'fields': fields}})

    return redirect(f'/admin-manage/{username}')

@admin_bp.route('/admin-update-content/<username>', methods=['POST'])
def update_content(username):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    user_site = user_sites_collection.find_one({'username': username})
    updates = {}

    for field in user_site.get('fields', []):
        if field['type'] == 'text':
            updates[field['name']] = request.form.get(field['name'], '')

        elif field['type'] == 'multiimage':
            files = request.files.getlist(field['name'])

            new_file_paths = []
            for img in files:
                if img.filename != '':
                    filename = secure_filename(img.filename)
                    img.save(os.path.join('static/uploads', filename))
                    new_file_paths.append(f'/static/uploads/{filename}')

            if new_file_paths:
                updates[field['name']] = new_file_paths
            else:
                updates[field['name']] = user_site.get(field['name'], [])

    if updates:
        user_sites_collection.update_one({'username': username}, {'$set': updates})
        print(f"Updated content for {username}: {updates}")
    else:
        print("No updates found.")

    return redirect(f'/admin-manage/{username}?t={int(time.time())}')

@admin_bp.route('/admin-remove-field/<username>/<field_name>', methods=['POST'])
def remove_field(username, field_name):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    user_site = user_sites_collection.find_one({'username': username})

    if user_site:
        updated_fields = [field for field in user_site.get('fields', []) if field['name'] != field_name]
        user_sites_collection.update_one({'username': username}, {'$set': {'fields': updated_fields}})
        user_sites_collection.update_one({'username': username}, {'$unset': {field_name: ""}})

    return redirect(f'/admin-manage/{username}')

@admin_bp.route('/admin-logout')
def admin_logout():
    session.pop('super_admin', None)
    return redirect('/admin-login')
