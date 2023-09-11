import pymongo
import datetime
import os
import json
import urllib.parse
import time
import csv
import pandas as pd
import numpy as np
from flask import Flask, request
from cryptography.fernet import Fernet
import hashlib
import shutil
import getpass
import base64
import ipaddress
import schedule
import threading
from pymongo.errors import DuplicateKeyError

app = Flask(__name__)

def generate_key(password):
    salt = b'salt'  # Salt for key derivation
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.urlsafe_b64encode(key)

def is_valid_ip_address(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False

def add_new_user():
    username = input("Enter new client's user name: ")
    db_name = input('Enter database name: ')
    password = input("Enter new client's password: ")
    ip_addr_set = input("Set client's machine ip address?[Y/n]")
    if ip_addr_set == 'Y' or ip_addr_set == 'y':
        ip_addr = input("New client's machine IP Address: ")
        while is_valid_ip_address(ip_addr) is False:
            ip_addr = input("IP address not valid. Enter client's machine IP Address again: ")
    else:
        ip_addr = ''
    encrypt_file([[username, db_name, password, ip_addr]])

def encrypt_file(data = None):
    output_file = 'my_protected_keys.bin'
    password = getpass.getpass('Enter password to update authorization file: ')

    if os.path.exists("./tmp/auths/" + output_file):
        if password != 'ffar_my_pass_cred':
            con = input("Wrong password. Continue[Y/n]?")
            if con == 'Y' or con == 'y':
                while password != 'ffar_my_pass_cred':
                    password = getpass.getpass('Re-enter your password: ')
            else:
                print("Failed adding new client's credentials!")
                return

    key = generate_key(password)
    cipher_suite = Fernet(key)
    if data is None:
        data = [
            ['water01','water_01_collection','mywater01','192.168.0.123'],
            ['soil01','soil_01_collection','mysoil01','192.168.0.129'],
            ['water02','water_02_collection','mywater02',''],
            ['et01', 'et_01_collection', 'myet01', '']]

    encrypted_data = []
    for row in data:
        row_bytes = '|'.join(row).encode('utf-8')
        encrypted_row = cipher_suite.encrypt(row_bytes)
        encrypted_data.append(encrypted_row)

    with open("./tmp/auths/" + output_file, 'ab') as file_out:
        for encrypted_row in encrypted_data:
            file_out.write(encrypted_row + b"\n")
    print("New client's credentials added successfully!")

def decrypt_file():
    password = 'ffar_my_pass_cred'
    key = generate_key(password)
    cipher_suite = Fernet(key)

    encrypted_data = []
    with open('./tmp/auths/my_protected_keys.bin', 'rb') as file:
        for line in file:
            line = line.rstrip(b'\n')
            encrypted_data.append(line)

    decrypted_data = []
    for encrypted_row in encrypted_data:
        decrypted_row = cipher_suite.decrypt(encrypted_row)
        row_values = decrypted_row.decode('utf-8').split('|')
        decrypted_data.append(row_values)

    return decrypted_data

def authenticate(received_username_data, received_pwd_data):
    decrypted_data = decrypt_file()
    collection_name = None
    filtered_rows = []

    for row in decrypted_data:
        if row[0] == received_username_data:
            filtered_rows.append(row)

    success_auth = False
    for rows in filtered_rows:
        if rows[2] == received_pwd_data:
            success_auth = True
            collection_name = rows[1]

    return success_auth, collection_name

def calculate_checksum(data):
    checksum = hashlib.sha3_256(data.encode()).hexdigest()
    return checksum

def verify_checksum(data, checksum):
    calculated_checksum = calculate_checksum(data)
    return calculated_checksum == checksum

def reset_count():
    filepath = './tmp/access_counts/'
    for f in os.listdir(filepath):
        with open(filepath + f, 'w') as file:
            file.write('0')
        print('[', datetime.datetime.now() ,']', "Access count reset to 0 for dataset: ", f)
    if len(os.listdir(filepath)) == 0:
        print('[', datetime.datetime.now() ,']', "Scheduled access count reset. No active datasets.")

def run_schedule2():
    # schedule.every().day.at("00:01").do(reset_count)
    schedule.every(10).minutes.do(reset_count)

    while True:
        schedule.run_pending()
        time.sleep(1)

def check_count(collection_name):
    threshold = 20
    count = 0
    filepath = './tmp/access_counts/' + collection_name + ".txt"

    try:
        with open(filepath, 'x') as file:
            file.write('1')
            return True
    except FileExistsError:
        with open(filepath, 'r') as file:
            count = int(file.read())
        if count >= threshold:
            return False
        count += 1
    with open(filepath, 'w') as file:
        file.write(str(count))
        print("Access count set to: ", count , 'for collection:' , collection_name)
    return True

@app.route("/add-data", methods=["POST"])
def add_data():

    payload = request.get_json()
    received_username_data = payload['username']
    received_pwd_data = payload['password']
    client_ip = request.remote_addr

    success_auth, collection_name = authenticate(received_username_data, received_pwd_data)

    if not success_auth:
        return 'ERROR 1: Data uploading failed. Authentication failed, please try again with valid username and password tokens'

    access_count = check_count(collection_name)
    # Uncomment for error 7
    # access_count = False
    if not access_count:
        return 'ERROR 7: Quota exceeded for number of file uploads. Try again tomorrow!'

    received_checksum = payload['checksum']
    received_csv_data = payload['csv_data']

    received_csv_data_str = str(received_csv_data)
    checksum_matched = verify_checksum(received_csv_data_str, received_checksum)

    # Uncomment for error 2
    # checksum_matched = False
    if not checksum_matched:
        return 'ERROR 2: Data corruption during transit detected. Send data again!'

    # Uncomment for error 4
    # collection_name = None
    if collection_name is None:
        return 'ERROR 4: Collection name mismatch. Contact CSU FFAR department at ffar.helpline@.cs.colostate.edu'

    isRunning = checkMongoDB()
    # Uncomment for error 3
    # isRunning = False

    new_file_name = collection_name + "." + datetime.datetime.today().strftime('%Y%m%d.%H%M%S')
    if not isRunning:
        save_new_file_to_local(received_csv_data, uploaded=False, file_name=new_file_name)
        return 'ERROR 3: Database down. Your file will be uploaded later. No need to send data again'

    return upload_data_to_mongodb(collection_name, received_csv_data, new_file_name)

def remove_id(data):
    for doc in data:
        doc.pop('_id', None)
    return data

def upload_data_to_mongodb(collection_name, received_csv_data, file_name):
        total_rows = len(received_csv_data)
        my_dummy_collection = initialize_databases(collection_name)
        try:
            result = my_dummy_collection.insert_many(received_csv_data)
        except pymongo.errors.PyMongoError as e:
            received_csv_data = remove_id(received_csv_data)
            response = "ERROR 6: Error while adding data to database mongoDB." + e
            save_new_file_to_local(received_csv_data, uploaded=False, file_name=file_name)
            return response

        received_csv_data = remove_id(received_csv_data)
        save_new_file_to_local(received_csv_data, uploaded=True, file_name=file_name)
        response = 'SUCCESS: %d/%d rows Have been inserted to %s collection.' % (len(result.inserted_ids),total_rows,collection_name)
        return response

def save_new_file_to_local(data, uploaded=False, file_name=None):
    if uploaded:
        path = "./tmp/data/uploaded/"
    else:
        path = "./tmp/data/pending/"

    filename = path + file_name + '.json'
    with open(filename, 'w') as file:
        json.dump(data, file)

    print(f"Incoming data saved to {filename}")

def upload_pending_files():
    if checkMongoDB():
        path = "./tmp/data/pending/"
        for f in os.listdir(path):
            print('[', datetime.datetime.now() ,']',"Scheduled uploading of pending file: ", f)
            with open(path + f, 'r') as file:
                loaded_data = json.load(file)

            collection_name = f.split(".")[0]
            upload_data_to_mongodb(collection_name, loaded_data, f.split(".json")[0])
            os.remove(path + f)
        if len(os.listdir(path)) == 0:
            print('[', datetime.datetime.now() ,']', "Scheduled uploading of pending file. No pending files")

def run_schedule():
    schedule.every(3).minutes.do(upload_pending_files)
    # schedule.every(6).hours.do(upload_pending_files)
    while True:
        schedule.run_pending()
        time.sleep(1)

def checkMongoDB():
    username = urllib.parse.quote_plus('root')
    password = urllib.parse.quote_plus('pUzUTfKMbw3z7v')
    mongo_url = 'mongodb://%s:%s@lattice-150:27018/' % (username, password)

    try:
        client = pymongo.MongoClient(mongo_url)
        db = client.test_3m_ffar
        response = db.command('ping')
        if response['ok'] == 1:
            return True
        else:
            return False
    except Exception as e:
        print('Error:', str(e))
        return False

def initialize_databases(collection_name="my_dummy_collection_testing"):
        username = urllib.parse.quote_plus('root')
        password = urllib.parse.quote_plus('pUzUTfKMbw3z7v')

        mongo_url = 'mongodb://%s:%s@lattice-150:27018/' % (username, password)
        sustainclient = pymongo.MongoClient(mongo_url)
        ffar_test_db_name = "test_3m_ffar"
        ffar_test_db = sustainclient[ffar_test_db_name]

        if collection_name is None:
            collection_name = "FFAR_Test_Collection_API"

        dataBase = ffar_test_db

        my_dummy_collection = dataBase[collection_name]
        # ffar_flux_collection = dataBase[collection_name]

        return my_dummy_collection

if __name__ == '__main__':
    schedule_thread = threading.Thread(target=run_schedule)     # Upload any pending files in every 6 hours
    schedule_thread.start()
    schedule_thread2 = threading.Thread(target=run_schedule2)   # Reset access count to 0 daily at 12.01am
    schedule_thread2.start()

    app.run(host="localhost", port=5000)

    # encrypt_file()
    # data = decrypt_file()
    # for d in data:
    #     print(d)

    # gunicorn_app = app
    # gunicorn_app.run()