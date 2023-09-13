Secure uploading of raw csv file using Rest API. It is flask based client-server program, which authenticates users detailes, uploads CSV files, checks for data tranmission corruption, maintains logs on client side, keep backups on server machine, and uploads csv to MongoDB database. 

# FFAR_API
1. server.py -  To start flask server on localhost, will keep listening to clients requests

         python3 server.py
   
3. client.py -  To run client program, simply call:

         python3 client.py

It will ask you for username and password to push new data. It username and password don't match the any row in encrypted passwords file (keeping record of all users' id/password) server will ask for logon details again. 

Another parameter is "file_name"  - which is absolute path of the csv file to be uploaded. If None, or value set it automatically set some file path. You can change that - "/s/lattice-180/b/nobackup/galileo/paahuni/ffar_data/fake_data.csv" to something else.  

client.py calls client_helper.py inside the code 

3. client_helper.py - This will make actual call to server program, it will read file provided from the path using pandas, then calculate checksum of entire file, and create json payload with checksum, csv data as dictionary, username, and password. Th call will be made to server, currently running locally - "http://localhost:5000/add-data".

It will wait for one of these responses - (a) Uploaded successfully, (b) ERROR 1 - Id/password incorrect (c) ERROR 2 -  Data corruption during transit detected (checksum mismatch) (d) ERROR 3 - MongoDB server down (e)  ERROR 4 - Collection name mismatch (f) ERROR 6 - Unsuccessful uploading error while adding data to database mongoDB. (g) ERROR 7 - Quota exceeded for number of file uploads per day/per database.

To get all username, password from passwork encrypted file, use following commands - 
   
    data = decrypt_file()
    for d in data:
         print(d)
         
One id/password: Username - soil01, password - mysoil01

To add new username and password, simply call -
    
    add_new_user()

It will ask new client's username, password, database name, you can optionally set ip_address. To update the global file of id and passwords, it will ask you for the your root password, which is 'ffar_my_pass_cred'
