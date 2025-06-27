import os
import time
from flask import Blueprint, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from db import users_collection, user_sites_collection, admins_collection

admin_bp = Blueprint('admin', __name__)

UPLOAD_FOLDER = 'static/uploads'

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

    selected_category = request.args.get('selected', 'all')

    if 'sections' not in user_site:
        user_site['sections'] = ['nav', 'hero', 'body', 'footer']
        user_sites_collection.update_one({'username': username}, {'$set': {'sections': user_site['sections']}})

    return render_template('admin_manage.html', content=user_site, username=username,
                           layouts=available_layouts, selected_category=selected_category)

@admin_bp.route('/admin-add-section/<username>', methods=['POST'])
def add_section(username):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    new_section = request.form['new_section']

    user_site = user_sites_collection.find_one({'username': username})
    sections = user_site.get('sections', [])

    if new_section not in sections:
        sections.append(new_section)
        user_sites_collection.update_one({'username': username}, {'$set': {'sections': sections}})

    return redirect(f'/admin-manage/{username}')

@admin_bp.route('/admin-remove-section/<username>/<section_name>', methods=['POST'])
def remove_section(username, section_name):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    user_site = user_sites_collection.find_one({'username': username})
    sections = user_site.get('sections', [])

    if section_name in sections:
        sections.remove(section_name)
        user_sites_collection.update_one({'username': username}, {'$set': {'sections': sections}})
        print(f"Section {section_name} removed successfully.")

    return redirect(f'/admin-manage/{username}')

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
    field_location = request.form['field_location']

    user_site = user_sites_collection.find_one({'username': username})
    fields = user_site.get('fields', [])

    if not any(field['name'] == new_field_name for field in fields):
        fields.append({'name': new_field_name, 'type': new_field_type, 'location': field_location})
        user_sites_collection.update_one({'username': username}, {'$set': {'fields': fields}})

    return redirect(f'/admin-manage/{username}')

@admin_bp.route('/admin-update-location/<username>/<field_name>/<new_location>', methods=['POST'])
def update_field_location(username, field_name, new_location):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    user_site = user_sites_collection.find_one({'username': username})
    fields = user_site.get('fields', [])

    for field in fields:
        if field['name'] == field_name:
            field['location'] = new_location
            break

    user_sites_collection.update_one({'username': username}, {'$set': {'fields': fields}})
    return redirect(f'/admin-manage/{username}')

@admin_bp.route('/admin-rename-field/<username>/<old_name>', methods=['POST'])
def rename_field(username, old_name):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    new_name = request.form['new_field_name']

    user_site = user_sites_collection.find_one({'username': username})
    fields = user_site.get('fields', [])
    updates = {}

    for field in fields:
        if field['name'] == old_name:
            field['name'] = new_name
            if old_name in user_site:
                updates[new_name] = user_site[old_name]
                updates[old_name] = None
            break

    user_sites_collection.update_one({'username': username}, {'$set': {'fields': fields}})
    if updates:
        user_sites_collection.update_one({'username': username}, {'$set': {k: v for k, v in updates.items() if v is not None}})
        user_sites_collection.update_one({'username': username}, {'$unset': {old_name: ""}})

    return redirect(f'/admin-manage/{username}?selected=all')

@admin_bp.route('/admin-update-content/<username>', methods=['POST'])
def update_content(username):
    if not session.get('super_admin'):
        return redirect('/admin-login')

    selected_category = request.form.get('selected_category', 'all')

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

    return redirect(f'/admin-manage/{username}?selected={selected_category}')

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
