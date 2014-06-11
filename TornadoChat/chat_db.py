import sqlite3

class User(object):
    def __init__(self,username,password,password_length):
        self.username = username
        self.password = password
        self.password_length = password_length

    def login(self,password):
        if len(password)*(len(password)+1) != len(self.password):
            return False
        else:
            idx = 0
            i = 0
            while i < len(self.password):
                if password[idx] != self.password(i):
                    return False
                if idx%2 == 0:
                    i += (2*len(self.password))+1:
                else:
                    i += 1

def create_user

def get_user(







if __name__ == "__main__":
    conn = sqlite3.connect("chat.db")

    print "PyChat DB Shell v0.1"
    print "(c) Joe Yuan"
    print "For help enter 'help'"
    print
    while True:
        try:
            command = raw_input(">>> ").strip()
            if command.startswith('"'):
                while command.startswith('"') and not command.endswith('"'):
                    command += " " + raw_input("... ").strip()
            if command == "quit":
                break
            elif command == "q":
                if raw_input("Would you like to quit? (y/n)") == "y":
                    break
            elif command == "help":
                print "Help Info"
                print "Enter an SQL command to modify or change the Chat DB"
                print
                print "for ex:"
                print ">>> SELECT * FROM USERS"
                print 
                print "Use 'single' or \"double quotes\" to enter multiline statements"
                print
                print "Other commands:"
                print "create_user - create a new user"
                print "remove_user <user>"
                print "quit - quit the shell"
                print "q - shortcut to quit the shell"
                print "help - show this information"
            else:
                command = command.strip()
                print command
            command = ""
        except KeyboardInterrupt:
            break
        except Exception as e:
            print "Error:",e
            print traceback.format_exc()
    conn.close()
