import hashlib
import argparse
import sys
import sqlite3
import string
import random
import hashlib

import os
from cryptography.fernet import Fernet


class EnigmaSafe:
    my_dir = os.path.dirname(__file__)
    data_base = os.path.join(my_dir, 'data_base.db')
    key_file = os.path.join(my_dir, 'key.key')
    KEY = ''
    
    # add to data-Base 
    def add_db(self, query ,values=''):
        connection = sqlite3.connect(self.data_base)
        cursor = connection.cursor()
        cursor.execute(query ,values)
        connection.commit()
        connection.close()
    

    # fetch data from data-base 
    def get_db(self,query , values='', fetch = 'one'):
        connection = sqlite3.connect(self.data_base)
        cursor = connection.cursor()
        cursor.execute(query , values)
        if fetch == 'one':
            data = cursor.fetchone()
        else:
            data = cursor.fetchall()
        connection.close()
        return data


    def verify_pin(self, pin):
        pin = hashlib.sha256(pin.encode()).hexdigest()
        s_pin = self.get_db("SELECT v_pin FROM cred")
        if pin == s_pin[0]:
            return True
        else:
            False



    # create default data base and tables
    def create_default_dataBase(self):
        try:
            if os.path.exists(self.data_base):
                return False
            else:
                query  = """ CREATE TABLE cred (
                            username CHAR(25) NOT NULL,
                            password CHAR(255) NOT NULL,
                            v_pin INTEGER(255) NOT NULL,
                            unblock_key CHAR(255) NOT NULL
                        ); """
                self.add_db(query,'')
                query  = """ CREATE TABLE passwords (
                            id INTEGER PRIMARY KEY,
                            name CHAR(25) NOT NULL,
                            password CHAR(255) NOT NULL,
                            description CHAR(1000) NOT NULL
                        ); """
                self.add_db(query,'')
                key = Fernet.generate_key()
                with open(self.key_file , 'wb') as f:
                    f.write(key)
                self.KEY = key
                print(key)
                return True
        except Exception as e:
            print(e)
            return None
        

    # configuration
    def configure(self, username, password, V_pin, unblock_key):
        password = hashlib.sha256(password.encode()).hexdigest()
        V_pin = hashlib.sha256(V_pin.encode()).hexdigest()
        query = 'INSERT INTO cred VALUES (?, ?, ?, ?)'
        value = (username,password,V_pin, unblock_key)
        try:
            self.add_db(query, value)
            return True
        except Exception as e:
            print(e)
            return None
        
    # check login handle
    def check_login(self, username, password):
        password = hashlib.sha256(password.encode()).hexdigest()
        query = 'SELECT username FROM cred WHERE username=? AND password=?'
        value = (username,password)
        user = self.get_db(query, value)
        return user


    # change login password  
    def change_password(self, username, password, new_password):
        password = hashlib.sha256(password.encode()).hexdigest()
        query = 'SELECT username FROM cred WHERE username = ? AND password = ?' 
        value = (username, password)
        user = self.get_db(query, value)
        if user:
            new_password = hashlib.sha256(new_password.encode()).hexdigest()
            self.add_db("UPDATE cred SET password = ?",(new_password,))
            return True
        else:
            return False


    # change varification code 
    def change_vcode(self, username, password, new_vcode):
        password =  hashlib.sha256(password.encode()).hexdigest()
        query = 'SELECT username FROM cred WHERE username = ? AND password = ?'
        value = (username, password)
        user = self.get_db(query, value)
        if user:
            new_vcode =  hashlib.sha256(new_vcode.encode()).hexdigest()
            self.add_db("UPDATE cred SET v_pin = ?",(new_vcode,))
            return True
        else:
            return False
        

    #add password to data-base
    def add_password(self, name, password, desc):
        try:
            fernet = Fernet(self.KEY)
            password = fernet.encrypt(password.encode()).decode()
            self.add_db('INSERT INTO passwords (name, password, description)  VALUES (?,?,?)',(name, password, desc))
            return True
        except Exception as e:
            print(e)
            return False
        


    # get all passwords to show in list 
    def get_passwords(self):
        try:
            data = self.get_db(query='SELECT id, name, description FROM passwords',values='',fetch='all')
            return data
        except Exception as e:
            print(e)
            return False
    

    # delete password 
    def delete_password(self,id, pin):
        try:
            if self.verify_pin(pin):
                self.add_db("DELETE FROM 'passwords' WHERE id = ?", (id,))
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return None
        

    def get_password(self,id, pin):
        try: 
            if self.verify_pin(pin):
                password = self.get_db("SELECT password FROM passwords WHERE id = ?", (id,))
                fernet = Fernet(self.KEY)
                password = fernet.decrypt(password[0].encode()).decode()
                return password
            else:
                return False
        except Exception as e:
            print(e)
            return None


































if __name__ == "__main__":
    parse = argparse.ArgumentParser()

    parse.add_argument('-P','--resetpassword',action="store_true",help="Reset Login password")
    parse.add_argument('-K','--showkey',action="store_true",help="Show unblock key")

    arg = parse.parse_args()
    num_args = len(sys.argv) - 1

    if num_args != 0:
        connection = sqlite3.connect('data_base.db')
        cursor = connection.cursor()
        if arg.resetpassword:
            characters = string.ascii_letters + string.digits
            password = ''.join(random.choice(characters) for _ in range(9))
            hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("UPDATE cred SET password = ?",(hash,))
            connection.commit()
            print('Password reset! \nPassword is: '+password)   
        if arg.showkey:
            cursor.execute("SELECT unblock_key FROM cred")
            key = cursor.fetchone()
            print("Your Unblock key is: "+key[0])
        
        connection.close()