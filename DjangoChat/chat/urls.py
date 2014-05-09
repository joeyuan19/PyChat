from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'login','chat.views.login_view',name='login'),
    url(r'room_destroy','chat.views.create_room_view',name='create'),
    url(r'room_create','chat.views.create_room_view',name='name'),
)


