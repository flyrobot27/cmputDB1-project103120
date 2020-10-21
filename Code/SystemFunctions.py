import sqlite3
import time
import curses
import curses.textpad

def editor():
    '''
    A simple editor for posting questions or answers. Returns the title and body of the post
    '''

    # initialize command line text editor with curses
    stdscr = curses.initscr()
    curses.noecho()      # displaying keys only when required
    curses.cbreak()      # no Enter key required
    stdscr.keypad(True)  # enable special keys

    begin_x = 0
    begin_y = 0
    rows, cols = stdscr.getmaxyx()
    win = curses.newwin(rows, cols, begin_y, begin_x)
    win.addstr(begin_y, begin_x, "Type your post here. Press Ctrl + G to switch and exit.")
    win.addstr(begin_y + 1, begin_x, "Title:")
    win.addstr(begin_y + 3, begin_x, "Body:")
    win.refresh()
    titlewin = win.subwin(1, cols ,begin_y + 2, begin_x)
    bodywin = win.subwin(rows - 7, cols ,begin_y + 4, begin_x)
    replywin = win.subwin(1, 2, rows - 2, begin_x + 22)
    redisplay = win.subwin(1, 22, rows - 2, begin_x)
    while True:
        title = curses.textpad.Textbox(titlewin, insert_mode=True).edit()
        body = curses.textpad.Textbox(bodywin, insert_mode=True).edit()
        redisplay.addstr(0, 0, "Exit and post? (y/N) ")

        redisplay.refresh()
        win.refresh()
        reply = curses.textpad.Textbox(replywin, insert_mode=True).edit(lambda x: 7 if x == 10 else x)
        if reply.strip() in ['y', 'Y', "yes", "Yes", "YES"]:
            break
        redisplay.clear()
        redisplay.refresh()
        replywin.clear()
        replywin.refresh()

    # restore configuration
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    return title, body


def search_post(conn, db, uid):
    ''' 
    search a post in the database. Return the matching posts 
    '''
    #TODO

def post_question(conn, db, uid):
    ''' 
    post a question to the database 
    '''
    title, body = editor()
    print(title)
    print(body)

def session(conn, db, uid):
    ''' User session entrance '''
    print("*------------*")
    print("Welcome back!")
    while True:
        print("Select an action:")
        print("1. Post a question.")
        print("2. Search for posts.")
        print("3. Logout")
        userInput = input("(1/2/3): ")
        print("*------------*")
        userInput.strip()
        if not userInput.isdigit():
            print()
            print("Unrecognized input. Please try again.")
            time.sleep(1)
            continue

        userInput = int(userInput)
        if userInput == 1:
            post_question(conn, db, uid)

        elif userInput == 2:
            search_post(conn, db, uid)

        elif userInput == 3:
            time.sleep(0.5)
            return