try:
    import sys
    import os
    import os.path
    import sqlite3
    from getpass import getpass
    from datetime import datetime
    import time
    import SystemFunctions
except ImportError as args:
    print("Import Error:", args)
    exit(1)


def register(conn, db):
    ''' 
    Creating new users.
    '''
    newID = input("Create user ID: ").strip()
    confirmID = input("Confirm user ID: ").strip()
    if newID == "":
        print()
        print("UserID cannot be empty!")
        print()
        time.sleep(0.5)
        return
    elif newID != confirmID:
        print()
        print("ID does not match!")
        print()
        time.sleep(0.5)
        return

    result = db.execute("SELECT users.uid FROM users WHERE UPPER(users.uid) = UPPER(?)", (newID,)).fetchall()
    if result == []:
        print()
        print("UserID Okay")
    else:
        print()
        print("User ID already exists. Please choose a different UID.")
        time.sleep(1)
        return 

    # obtain user info
    while True:
        password = getpass("Enter new password (no blankspace): ").strip()
        confirm_password = getpass("Confirm your password: ").strip()
        if password != confirm_password:
            print("Password does not match")
            print()
            time.sleep(0.5)
        elif password == "":
            print("Password cannot be empty!")
            print()
            time.sleep(0.5)
        else:
            break

    while True:
        newName = input("Enter your name: ")
        if newName.strip() == '':
            print("Name cannot be empty!")
        else:
            break

    while True:
        city = input("Enter your city: ")
        if city.strip() == '':
            print("City cannot be empty!")
        else:
            break

    crdate = datetime.date(datetime.now()) # crdate = current date

    db.execute("INSERT INTO users VALUES (?,?,?,?,?)", (newID, newName, password, city, crdate))
    conn.commit()
    print("User {0} created!".format(newID))

    return SystemFunctions.session(conn, db, newID)


def login(conn, db):
    ''' 
    Existing users login.
    '''

    userID = input("Enter user id (uid): ").strip() # get UID. Remove spaces
    password = getpass("Enter password: ").strip() # get password
    result = db.execute("SELECT users.uid FROM users WHERE UPPER(uid) = UPPER(?)", (userID,)).fetchall()

    if result != []:    # non empty return, username is in database
        var = (userID, password)
        result = db.execute("SELECT users.uid FROM users WHERE UPPER(uid) = UPPER(?) AND pwd = ?", var).fetchall()

        if result == []: # indicating the password and username does not match
            print("Username or password is incorrect.")
            time.sleep(1)
            return 
        else:
            uid = result[0][0]
    else:
        print("User does not exist.")
        time.sleep(1)
        return 

    print("login successful")

    return SystemFunctions.session(conn, db, uid)

def main():
    ''' 
    Prompt the login screen (cmd). Check user Input
    '''

    # connect to the database
    try:
        # obtain DB file path
        if len(sys.argv) != 2 or sys.argv[1] in ("help", "--help", "-h"):
            print("Usage: python3 main.py [.db file]")
            exit(0)
        db_path = sys.argv[1]

        # check if db exists
        if not os.path.isfile(db_path): 
            raise IOError("Failed to locate database")

    except IOError as args:
        print("Error: ", args)
        exit(1)

    # connect to database
    conn = sqlite3.connect(db_path)
    db = conn.cursor()
    print("*-----------------------*")
    while True:
        print("Welcome to community QAN!")
        print("Please select an action:")
        print("1. Login")
        print("2. Register")
        print("3. Quit")
        userInput = input("Select your action (1/2/3): ")
        
        userInput.strip()
        if not userInput.isdigit():
            print()
            print("Unrecognized input. Please try again.")
            print("*-----------------------*")
            time.sleep(1)
            continue

        userInput = int(userInput)
        if userInput == 1:
            login(conn, db)
            print("*-----------------------*")
        elif userInput == 2:
            register(conn, db)
            print("*-----------------------*")

        elif userInput == 3:
            print("GoodBye!")
            exit(0)
        else:
            print()
            print("Unrecognized input. Please try again.")
            time.sleep(1)
        


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("User interrupted.")
        print("Bye")
        exit(0)
    except Exception as args:
        print()
        print("Fatal Error:",args)
        os.system("stty sane") # reset the shell
        exit(1)
