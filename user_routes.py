import os
from flask import Blueprint, render_template, request, redirect, session
from db import users_collection, user_sites_collection

user_bp = Blueprint('user', __name__)

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

    return render_template('user_dashboard.html', content=user_site, username=username)

@user_bp.route('/user-logout')
def user_logout():
    session.pop('user_logged_in', None)
    return redirect('/user-login')
