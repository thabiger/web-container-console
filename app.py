from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from flask_socketio import SocketIO, emit
import subprocess
import os
from cryptography.fernet import Fernet

# Add default values to the PATH environment variable
default_paths = ['/usr/local/bin', '/usr/bin', '/bin', '/usr/sbin', '/sbin']
os.environ['PATH'] = ':'.join(default_paths + os.environ.get('PATH', '').split(':'))

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app)

# Generate a secret if SECURE=1 is set
if os.getenv('SECURE') == '1':
    secret_key = os.getenv("SECRET_KEY", Fernet.generate_key().decode())
    print(f"Generated secret key: {secret_key}")
    app.config['SECRET_KEY'] = secret_key
else:
    app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():
    if os.getenv('SECURE') == '1' and 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['secret'] == app.config['SECRET_KEY']:
            session['authenticated'] = True
            response = make_response(redirect(url_for('index')))
            response.set_cookie('authenticated', 'true')
            return response
        else:
            return 'Invalid secret key', 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('authenticated')
    return response

@socketio.on('execute_command')
def handle_command(data):
    command = data['command']
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        result = e.output
    emit('command_output', {'output': result})

@socketio.on('complete_command')
def handle_completion(data):
    command = data['command']
    completions = get_completions(command)
    emit('command_completions', {'completions': completions})

def get_completions(command):
    words = command.split()
    if not words:
        return []
    try:
        prefix = words[-1]
        completions = subprocess.check_output(f"compgen -A file -A command -A alias -A function -- {prefix}", shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        path_binaries = subprocess.check_output(f"compgen -c -- {prefix}", shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        all_completions = completions.splitlines() + path_binaries.splitlines()
        return [comp for comp in all_completions if comp.startswith(prefix)]
    except subprocess.CalledProcessError:
        return []

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)), allow_unsafe_werkzeug=True)
