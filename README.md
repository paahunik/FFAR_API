Secure uploading of raw CSV files using Rest API. It is flask flask-based client-server program, which authenticates users' details, uploads CSV files, checks for data transmission corruption, maintains logs on the client side, keeps backups on the server machine, and uploads CSV to MongoDB database. 

# FFAR_API
1. server.py -  To start the flask server on localhost, will keep listening to the client's requests

         python3 server.py
   
3. client.py -  To run the client program, simply call:

         python3 client.py

It will ask you for a username and password to push new data. If the username and password don't match any row in the encrypted passwords file (keeping a record of all users' IDs/passwords) server will ask for login details again. 

Another parameter is "file_name"  - which is the absolute path of the CSV file to be uploaded. If None, or value set it automatically sets some file path. You can change that - "/s/lattice-180/b/nobackup/galileo/paahuni/ffar_data/fake_data.csv" to something else.  

client.py calls client_helper.py inside the code 

3. client_helper.py - This will make an actual call to the server program, It will read the file provided from the path using pandas, then calculate the checksum of the entire file, and create JSON payload with checksum, CSV data as dictionary, username, and password. The call will be made to the server, currently running locally - "http://localhost:5000/add-data".

It will wait for one of these responses - (a) Uploaded successfully, (b) ERROR 1 - Id/password incorrect (c) ERROR 2 -  Data corruption during transit detected (checksum mismatch) (d) ERROR 3 - MongoDB server down (e)  ERROR 4 - Collection name mismatch (f) ERROR 6 - Unsuccessful uploading error while adding data to database mongoDB. (g) ERROR 7 - Quota exceeded for number of file uploads per day/per database.

To get all usernames, and passwords from password encrypted file, use the following commands - 
   
    data = decrypt_file()
    for d in data:
         print(d)
         
One ID/password: Username - soil01, password - mysoil01

To add a new username and password, simply call -
    
    add_new_user()

It will ask new client's username, password, and database name, you can optionally set ip_address. To update the global file of id and passwords, it will ask you for your root password, which is 'ffar_my_pass_cred'
