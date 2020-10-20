try:
    import sqlite3

except ImportError as args:
    print("Error:", args)
    exit(1)

def login(db):
    userName = input("Enter user name: ")
    password = input("Enter password: ")

def register(db):
    newName = input("Create user name: ")
    db.execute("SELECT name FROM users WHERE name=?", newName)
    print(db.fetchone())


def main():
    ''' prompt the login screen (cmd). Check user Input'''
    # connect to the database
    try:
        conn = sqlite3.connect("p1.db")
        db = conn.cursor()
    except IOError as args:
        print("Error:", args)
        exit(1)

    userInput = 0
    print("Welcome!")
    print("Please select an action:")
    
    while True:
        print("1. Login")
        print("2. Register")
        print("3. Quit")
        userInput = input("Type your action (1/2/3):")
        
        userInput.strip()
        if not userInput.isdigit():
            print("Unrecognized input. Please try again:")
            continue

        userInput = int(userInput)
        if userInput == 1:
            login(db)

        elif userInput == 2:
            register(db)

        elif userInput == 3:
            print("Bye")
            exit(0)
        else:
            print("Unrecognized input. Please try again:")
        


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("User interrupted.")
        print("Bye")
        exit(0)
