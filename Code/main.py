import sqlite3



def main():
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
        if userInput not in [1,2,3]:
            print("Unrecognized input. Please try again:")
        elif userInput == 3:
            print("Bye")
            exit(0)
        else:
            break

    print("End:",userInput)


if __name__ == '__main__':
    main()

