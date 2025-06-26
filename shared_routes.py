import os
import re
from flask import Blueprint, render_template_string
from db import users_collection, user_sites_collection

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/website/<username>')
def user_website(username):
    user_site = user_sites_collection.find_one({'username': username})
    if not user_site:
        return 'Website not found', 404

    layout = user_site.get('layout', 'layout1')
    layout_path = f'templates/layouts/{layout}.html'

    if not os.path.exists(layout_path):
        return 'Layout file not found', 404

    with open(layout_path, 'r') as file:
        layout_content = file.read()

    # Build a dictionary of field content
    variables = {}
    for field in user_site.get('fields', []):
        if field['type'] == 'multiimage':
            images = user_site.get(field['name'], [])
            variables[field['name']] = images[0] if images else ''
        else:
            variables[field['name']] = user_site.get(field['name'], '')

    # Custom tag replacement function
    def replace_pagelet(match):
        field_name = match.group(1)
        return variables.get(field_name, '')

    # Replace all custom tags like <p:pagelet title="fieldname" />
    processed_layout = re.sub(r'<p:pagelet title=[\'"](.*?)[\'"]\s*/?>', replace_pagelet, layout_content)

    return render_template_string(processed_layout)
