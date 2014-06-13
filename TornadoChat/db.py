import sqlite3
import traceback
import getpass
import random

DB_NAME = "chat.db"

class ChatUser(object):
    @classmethod
    def get_user(cls,username,logged_in=False,session_token=''):
        user = get_user(username)
        if user is None:
            return user
        return cls(user[0],user[1],logged_in,session_token)

    @classmethod
    def get_all(cls):
        return [cls(user[0],user[1]) for user in get_all_users()]
    
    @classmethod
    def create_user(cls,username,password):
        if check_for_user(username):
            raise UserAlreadyExistsError("A user with this name already exists")
        instance = cls(username,mask_password(password))
        insert_user(instance.username,instance.password)
        return instance

    def __init__(self,username,password,logged_in=False,session_token=''):
        self.username = username
        self.password = password
        self._loggedin = logged_in
        self.session_token = session_token

    def delete(self):
        if self._loggedin:
            delete_user(self.username)
    
    def change_password(self,new_password):
        if not self.loggedin():
            return
        self.password = mask_password(new_password)
        self.save()

    def loggedin(self):
        return self._loggedin

    def login(self,password):
        self._loggedin = self.verify_password(password)
        return self._loggedin

    def verify_password(self,password):
        if len(password)*(len(password)+1) != len(self.password):
            return False
        else:
            idx = 0
            i = 0
            while i < len(self.password):
                if password[idx] != self.password[i]:
                    return False
                if idx%2 == 0:
                    i += (2*len(self.password))+1
                else:
                    i += 1
            return True

# Random Char Generation

def random_char():
    return chr(random.choice(range(33,95)+range(96,127)))

def random_string(n):
    s = ""
    for i in range(n):
        s += random_char()
    return s

# Password masking
#   dog -> d######og###
# where '#' is a random character
# the pattern is built in chunks:
# d + ###
# ### + o
# g + ###
# even/odd determins before or after
# length of original password determines
# length of random string.

def mask_password(password):
    masked = ""
    L = len(password)
    for i in range(L):
        if i%2 == 0:
            masked += password[i] + random_string(L)
        else:
            masked += random_string(L) + password[i]
    return masked

class UserAlreadyExistsError(Exception):
    pass

class InvalidSQLiteError(Exception):
    pass

# DB calls, they are double wrapped candies

def get_user(username):
    return execute(_get_user,username)

def _get_user(cur,username):
    _sql = """
    SELECT * FROM users WHERE username=:username
    """
    cur.execute(_sql,{"username":username})
    return cur.fetchone()

def get_all_users():
    return execute(_get_all_users)

def _get_all_users(cur):
    _sql = """
    SELECT * FROM users
    """
    cur.excute(_sql)
    return cur.fetchall()

def check_for_user(username):
    return execute(_check_for_user,username)

def _check_for_user(cur,username):
    _sql = """
    SELECT username FROM users WHERE username=:username
    """
    cur.execute(_sql,{"username":username})
    return cur.fetchone() is not None

def insert_user(username,password):
    return execute(_insert_user,username,password)

def _insert_user(cur,username,password):
    if check_for_user(username):
        raise UserAlreadyExistsError("The user " + username + " already exists")
    else:
        _sql = """
        INSERT INTO users VALUES (:username,:password)
        """
        cur.execute(_sql,{"username":username,"password":password})

def delete_user(username):
    return execute(_delete_user,username)

def _delete_user(cur,username):
    _sql = """
    DELETE FROM users WHERE username=':username'
    """
    cur.execute(_sql,{"username":username})

def change_password(username,new_password):
    return execute(_change_password,username,new_password)

def _change_password(cur,username,new_password):
    _sql = """
    UPDATE users
    SET password=':newpassword'
    WHERE username=':username'
    """
    cur.execute(_sql,{'username':username,'newpassword':new_password})


def execute(f,*args):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    val = None
    try:
        val = f(cur,*args)
    except Exception as e:
        print traceback.format_exc()
    conn.commit()
    conn.close()
    return val

def executemany(f,*args):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    val = None
    try:
        val = f(cur,*args)
    except Exception as e:
        print traceback.format_exc()
    conn.commit()
    conn.close()
    return val

def execute_raw(_sql):
    try:
        conn = None
        #if not sqlite3.complete_statement(_sql):
        #    raise InvalidSQLiteError('"'+_sql+'" is an invalid sqlite3 statement')
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        val = None
        cur.execute(_sql)
        if _sql.lower().startswith("select"):
            val = cur.fetchall()
        conn.commit()
        conn.close()
    finally:
        if conn:
            conn.close()
    return val


def init():
    execute(_init)

def _init(cur):
    _sql = """
    CREATE TABLE users (username,password)
    """
    cur.execute(_sql)

if __name__ == "__main__":
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
                command = command[1:-1]
            if command == "quit":
                break
            elif command == "q":
                if raw_input("Would you like to quit? (y/n)") == "y":
                    break
            elif command == "init":
                init()
            elif command == "create_user":
                username = raw_input("Username: ")
                password = getpass.getpass()
                user = ChatUser.create_user(username,password)
            elif command.startswith("delete_user"):
                username = command[command.find(" ")+1:]
                delete_user(username)
            elif command.startswith("has_user"):
                username = command[command.find(" ")+1:]
                print check_for_user(username)
            elif command == "help":
                print "Help Info"
                print "Enter an SQL command to modify or change the Chat DB"
                print
                print "for ex:"
                print ">>> SELECT * FROM TABLE"
                print 
                print "Use 'single' or \"double quotes\" to enter multiline statements"
                print
                print "Other commands:"
                print "create_user - create a new user"
                print "delete_user <user> - removes <user> from the db"
                print "has_user <user> - checks for user <user>"
                print "quit - quit the shell"
                print "q - shortcut to quit the shell"
                print "help - show this information"
                print "init - initialize the db"
            else:
                command = command.strip()
                if len(command) > 0:
                    val = execute_raw(command)
                    if val is not None:
                        print val
        except KeyboardInterrupt:
            print "Bye!"
            break
        except Exception as e:
            print "Error:",e
            print traceback.format_exc()
        finally:
            command = ""
