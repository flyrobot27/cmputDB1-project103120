try:
    import os.path
    import sqlite3
    from getpass import getpass
    from datetime import datetime
    import time
    import SystemFunctions
except ImportError as args:
    print("Error:", args)
    exit(1)


def register(conn, db):
    ''' 
    Creating new users.
    '''
    newName = input("Create user name: ").strip()
    result = db.execute("SELECT users.uid FROM users WHERE UPPER(users.name) = UPPER(?)", (newName,)).fetchall()
    if result == []:
        print()
        print("Username Okay")
    else:
        print()
        print("User already exists")
        time.sleep(1)
        return 

    # obtain user info
    password = getpass("Enter new password (no blankspace):").strip()

    while True:
        city = input("Enter your city: ")
        if city.strip() == '':
            print("City cannot be empty!")
        else:
            break

    crdate = datetime.date(datetime.now()) # crdate = current date

    # find last uid
    maxuid = db.execute("SELECT MAX(uid) FROM users").fetchall()
    if maxuid[0][0] != None:
        uidintstr = maxuid[0][0][1:]
        if uidintstr == "999":
            print("No more users can be created.")
            return 

        uidint = int(uidintstr) + 1
        newuid = "u" + str(uidint).zfill(len(uidintstr))

    else:
        newuid = "u000"

    db.execute("INSERT INTO users VALUES (?,?,?,?,?)", (newuid, newName, password, city, crdate))
    conn.commit()
    print("User {0} created!".format(newName))

    return SystemFunctions.session(conn, db, newuid)


def login(conn, db):
    ''' 
    Existing users login.
    '''

    userName = input("Enter user name: ").strip() # get username. Remove spaces
    password = getpass("Enter password: ").strip() # get password
    result = db.execute("SELECT users.uid FROM users WHERE UPPER(name) = UPPER(?)", (userName,)).fetchall()

    if result != []:    # non empty return, username is in database
        var = (userName, password)
        result = db.execute("SELECT users.uid FROM users WHERE UPPER(name) = UPPER(?) AND pwd = ?", var).fetchall()

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
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "p1.db")

        # check if p1.db exists
        if not os.path.isfile(db_path): 
            raise IOError

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
        print("User interrupted.")
        print("Bye")
        exit(0)
