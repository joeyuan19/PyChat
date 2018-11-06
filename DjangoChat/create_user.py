from chat.models import ChatUser

correct = False

while not correct:
    u_name = raw_input("username: ")
    p_word = raw_input("password: ")
    
    print "username:",u_name,"password:",p_word
    correct = "y" == raw_input("correct? (y/n)")
try:
    user = ChatUser.objects.get(name=u_name)
    print "User exists -- username:",user.name,"password",user.password
except:
    a = ChatUser.create(name=u_name,password=p_word)
    a.save()
    print "User created -- username:",a.name,"password:",a.password




