from client_helper import insert_data_to_mongo as upload_data
import getpass

if __name__ == '__main__':
    username = None
    password = None

    if username is None or password is None:
        username = input("Enter your username: ")
        password = getpass.getpass('Enter your password: ')

    filename = None
    upload_data(file_name=filename, username=username, password=password)

    # naming structure?





