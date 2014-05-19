from django.contrib import admin
from chat.models import Room, ChatUser


class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_id','isactive','addr','user_list')

class ChatUserAdmin(admin.ModelAdmin):
    list_display = ('name','password','isactive')

admin.site.register(Room,RoomAdmin)
admin.site.register(ChatUser,ChatUserAdmin)

