import requests
import pandas as pd
import hashlib
import csv
import datetime
import pip
import getpass

# Hashing Algorithm: SHA3
def calculate_checksum(data):
    checksum = hashlib.sha3_256(data.encode()).hexdigest()
    return checksum

def insert_data_to_mongo(file_name=None, username=None, password = None, counter = 0):
    if counter > 5:
        print("ERROR 8: Reached maximum (5) requests to upload file. Data corruption detected during transmission. Try again later!")
        return -1

    filename = './client_store/response.log'
    if file_name is None:
        file_name = "/s/lattice-180/b/nobackup/galileo/paahuni/ffar_data/fake_data.csv"

    df = pd.read_csv(file_name)
    data = df.to_dict(orient="records")
    num_rows = df.shape[0]

    checksum = calculate_checksum(str(data))
    payload = {
        'checksum': checksum,
        'csv_data': data,
        'username': username,
        'password': password
    }
    url = "http://localhost:5000/add-data"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    current_date = datetime.datetime.today().strftime("%Y-%m-%d")
    current_time = datetime.datetime.today().strftime("%H:%M:%S")
    if response.status_code == 200:
        print(response.text)
        responseCode = response.text.split(":")[0]
        if responseCode == 'ERROR 1':
            continueD = input("Retry uploading data? [Y/n]")
            if continueD == 'Y' or continueD == 'y':
                username = input("Enter your username: ")
                password = getpass.getpass('Enter your password: ')
                insert_data_to_mongo(file_name=file_name, username=username, password=password)

        if responseCode == 'ERROR 2':
            counter += 1
            out = insert_data_to_mongo(file_name=file_name, username=username, password=password, counter=counter)
            if out == -1:
                return

        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            if responseCode[:3] == 'ERR':
                writer.writerows([['FAIL', str(num_rows), current_date, current_time, file_name, response.text]])
            else:
                writer.writerows([['OK', str(num_rows), current_date, current_time, file_name, response.text]])
    else:
        print("Request failed with status code:", response.text)
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows([['FAIL', str(num_rows), current_date, current_time, file_name, 'ERROR 5: Back-end Server down. Try again later.']])
    return None