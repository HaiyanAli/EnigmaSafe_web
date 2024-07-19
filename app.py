from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
import string
import random
import hashlib
from cryptography.fernet import Fernet
from EnigmaSafe import EnigmaSafe


eg = EnigmaSafe()
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

registrantion = False

login_attempt = 0



if os.path.exists(eg.key_file):
    registrantion = True
    with open(eg.key_file, 'r') as f:
        eg.KEY = f.read().encode()


    











def unblock_key_gen():
    characters = string.ascii_letters + string.digits
    key = ''.join(random.choice(characters) for _ in range(32))
    return key











@app.route('/')
def hello_world():
    if login_attempt == 3:
        return render_template('block.html')
    elif not registrantion:
        return render_template('retgistration.html')
    elif 'username' in session:
        return render_template('home.html')
    elif registrantion:
        return render_template('login.html')



@app.route('/setup', methods=['POST'])
def setup():
    global registrantion
    if request.method == "POST" and registrantion == False:
        data = request.get_json() 
        email = data['email']
        username = data['username']
        password = data['password']
        confirm_password = data['c_password']
        v_pin = data['v_pin']

        if not email:
            return jsonify({'success': False,'error': 'Please Enter Email!'})
        elif not username:
            return jsonify({'success': False,'error': 'Please Enter Username!'})
        elif not password:
            return jsonify({'success': False,'error': 'Please Enter Password!'})
        elif not confirm_password:
            return jsonify({'success': False,'error': 'Please Enter Confirm Password!'})
        elif not v_pin:
            return jsonify({'success': False,'error': 'Please Enter verification Pin!'})
        
        elif not v_pin.isdigit():
            return jsonify({'success': False,'error': 'Verification Pin should be numeric!'})
        
        elif len(password) < 8:
            return jsonify({'success': False,'error': 'Password length should be at least 8 characters.'})
        elif password != confirm_password:
            return jsonify({'success': False,'error': 'Password Not Matched!'})

        elif not eg.create_default_dataBase():
            return jsonify({'success': False,'error': 'Something Wrong! check error logs'})

        unblock_key = unblock_key_gen()
        res = eg.configure(username,password,v_pin,unblock_key)
        if res == None:
            os.remove(eg.data_base)
            return jsonify({'success': False,'error': 'Something Wrong! check error logs'})
        elif res:
            registrantion = True
            return jsonify({'success': True,'error': '', 'key': unblock_key})




@app.route('/login', methods=['POST'])
def login():
    global registrantion
    global login_attempt
    if request.method == "POST" and registrantion == True:
        if login_attempt == 3:
            return jsonify({'success': True,'error': ''})
        data = request.get_json() 
        username = data['username']
        password = data['password']
        remember = data['remember']
        if not username:
            return jsonify({'success': False,'error': 'Please Enter Username!'})
        elif not password:
            return jsonify({'success': False,'error': 'Please Enter Password!'})
        login_attempt += 1
        user = eg.check_login(username, password)
        if user:
            session['username'] = username
            if remember == True:
                session.permanent = True
            login_attempt = 0
            return jsonify({'success': True,'error': ''})
        else:
            return jsonify({'success': False,'error': 'Inalid Username Or Password!'})



@app.route('/unblock', methods =['POST'])
def unblock():
    global login_attempt
    if request.method == 'POST':
        data = request.get_json()
        key = data['key']
        connection = sqlite3.connect(eg.data_base)
        cursor = connection.cursor()
        cursor.execute('SELECT unblock_key FROM cred WHERE unblock_key = ?', (key,))
        unblock = cursor.fetchone()
        connection.close()
        if unblock:
            login_attempt=0
            return jsonify({'key':True})
        else:
            return jsonify({'key':False})



@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' in session:
        if request.method == 'POST':
            data = request.get_json()
            username = data['username']
            password = data['password']
            new_password = data['newpassword']
            c_new_password = data['c_newpassword']

            if not username:
                return jsonify({'success': False,'error': 'Please Enter Username!'})
            elif not password:
                return jsonify({'success': False,'error': 'Please Enter Paswsword!'})
            elif not new_password:
                return jsonify({'success': False,'error': 'Please Enter New Paswsword!'})
            elif not c_new_password:
                return jsonify({'success': False,'error': 'Please Enter New Confirm Paswsword!'})
            elif new_password != c_new_password:
                return jsonify({'success': False,'error': "Paswsword dosen't Matched!"})
            elif len(new_password) < 8:
                return jsonify({'success': False,'error': "Password length should be at least 8 characters."})


            if eg.change_password(username, password, new_password):
                return jsonify({'success': True,'error': ""})
            else:
                return jsonify({'success': False,'error': "Invalid Username or Password!"})

    else:
        return redirect('/')


@app.route('/change_vcode', methods=['POST'])
def change_vcode():
    if 'username' in session:
        if request.method == 'POST':
            data = request.get_json()
            username = data['username']
            password = data['password']
            new_vcode = data['new_vcode']
            c_new_vcode = data['c_new_vcode']

            if not username:
                return jsonify({'success': False,'error': 'Please Enter Username!'})
            elif not password:
                return jsonify({'success': False,'error': 'Please Enter Paswsword!'})
            elif not new_vcode:
                return jsonify({'success': False,'error': 'Please Enter New Verification Code!'})
            elif not c_new_vcode:
                return jsonify({'success': False,'error': 'Please Enter New Confirm Verification Code!'})
            elif new_vcode != c_new_vcode:
                return jsonify({'success': False,'error': "Code dosen't Matched!"})
            elif len(new_vcode) != 4:
                return jsonify({'success': False,'error': "Code length should be 4 Digit."})

            
            if eg.change_vcode(username, password, new_vcode):
                return jsonify({'success': True,'error': ""})
            else:
                return jsonify({'success': False,'error': "Invalid Username or Password!"})

    return redirect('/')


@app.route('/add_password', methods = ['POST'])
def add_password():
    if 'username' in session:
        if request.method == 'POST':
            data = request.get_json()
            name = data['name']
            password = data['password']
            description = data['desc']

            if not name:
                return jsonify({'success': False,'error': 'Please Enter Password Name!'})
            elif not password:
                return jsonify({'success': False,'error': 'Please Enter Password!'})
            elif not description:
                description = 'none'

            if eg.add_password(name, password, description):
                return jsonify({'success': True,'error': ''})
            else:
                return jsonify({'success': False,'error': "Some Thing Wrong! Password not Added!"})
    else:
        return redirect('/')



@app.route('/get_passwords')
def get_passwords():
    if 'username' in session:
        data = eg.get_passwords()
        if data == False:
            return jsonify({'success': False,'error': "Some Thing Wrong! Can't Fetch Passwords "})
        else:
            return jsonify({'data':data})


@app.route('/delete_password', methods = ['POST'])
def delete_password():
    if 'username' in session:
        if request.method == 'POST':
            data = request.get_json()
            id =data['id']
            v_code = data['v_code']
            if not id:
                return jsonify({'success': False,'error': "Some Thing Wrong! Password Not deleted!  "})
            
            data = eg.delete_password(id, v_code)
            if data == False:
                return jsonify({'success': False,'error': "In-Valid Verification Pin! "})
            elif data == None:
                return jsonify({'success': False,'error': "Some Thing Wrong! Password Not deleted! "})
            else:
                return jsonify({'success': 'Password Deleted!','error': ""})

    return redirect('/')



@app.route('/get_password',)
def get_password():
    if 'username' in session:
        if request.method == 'GET':
            id =request.args.get('id')
            v_code = request.args.get('v_code')
            if not id:
                return jsonify({'success': False,'error': "Some Thing Wrong! Password Not deleted!  "})
            
            data = eg.get_password(id, v_code)
            if data == False:
                return jsonify({'success': False,'error': "In-Valid Verification Pin! "})
            elif data == None:
                return jsonify({'success': False,'error': "Some Thing Wrong! Password Not Copyed!"})
            else:
                return jsonify({'success': 'Password Copyed!','error': '', 'password':data})

    return redirect('/')













@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')



app.run(host='192.168.1.200', port=80, debug=True)

