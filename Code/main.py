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

def return_yes_no(userInput):
    ''' 
    Check yes/no input. If yes, return 1. If no, return 0. If undentified, return 2
    '''

    if userInput in ['N', 'n', "no", "No", "NO"]:
        return 0
    elif userInput in ['y', 'Y', "Yes", "yes", "YES"]:
        return 1
    else:
        return 2


def register(conn, db):
    ''' 
    Creating new users. Return False if user want to quit the program, True if otherwise.
    '''

    while True:
        newName = input("Create user name: ").strip()
        result = db.execute("SELECT users.uid FROM users WHERE users.name = ?", (newName,)).fetchall()
        if result == []:
            print("Username Okay")
            break
        print()
        print("User already exists")
        time.sleep(1)

    # obtain user info
    password = getpass("Enter new password (no blankspace):").strip()
    city = input("Enter your city: ")
    crdate = datetime.date(datetime.now()) # crdate = current date

    # find last uid
    maxuid = db.execute("SELECT MAX(uid) FROM users").fetchall()
    uidintstr = maxuid[0][0][1:]
    if uidintstr == "999":
        print("No more users can be created.")
        return True

    uidint = int(uidintstr) + 1
    newuid = "u" + str(uidint).zfill(len(uidintstr))

    db.execute("INSERT INTO users VALUES (?,?,?,?,?)", (newuid, newName, password, city, crdate))
    conn.commit()
    print("User {0} created!".format(newName))

    return SystemFunctions.session(conn, db, newuid)



def login(conn, db):
    ''' 
    Existing users login. Return False if user want to quit the program, True if otherwise. 
    '''

    while True:
        userName = input("Enter user name: ").strip() # get username. Remove spaces
        password = getpass("Enter password: ").strip() # get password
        result = db.execute("SELECT users.uid FROM users WHERE name = ?", (userName,)).fetchall()

        if result != []:    # non empty return, username is in database
            var = (userName, password)
            result = db.execute("SELECT users.uid FROM users WHERE name = ? AND pwd = ?", var).fetchall()

            if result == []: # indicating the password and username does not match
                print("Username or password is incorrect.")
                time.sleep(1)
                while True:
                    retry = input("Retry? (y/n): ").strip()
                    if not return_yes_no(retry):
                        return True
                    elif return_yes_no(retry) == 1:
                        break
            else:
                uid = result[0]
                break
        else:
            print("User does not exist.")
            time.sleep(1)
            while True:
                retry = input("Create user? (y/n)") 
                if return_yes_no(retry) == 1: # if user want to create a new user
                    return register(conn, db) 
                elif return_yes_no(retry) == 0:
                    return True

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

    print("Welcome!")
    
    while True:
        print()
        print("Please select an action:")
        print("1. Login")
        print("2. Register")
        print("3. Quit")
        userInput = input("Select your action (1/2/3):")
        
        userInput.strip()
        if not userInput.isdigit():
            print()
            print("Unrecognized input. Please try again.")
            time.sleep(1)
            continue

        userInput = int(userInput)
        if userInput == 1:
            if not login(conn, db):
                exit(0)

        elif userInput == 2:
            if not register(conn, db):
                exit(0)

        elif userInput == 3:
            print("Bye")
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
