from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^login/','chat.views.login_view',name='login'),
    url(r'^logout/','chat.views.logout_view',name='logout'),
    url(r'^room_create/','chat.views.create_room_view',name='create'),
    url(r'^join/','chat.views.create_room_view',name='join'),
    url(r'^room_list/','chat.views.get_room_listing',name='room_list'),
    url(r'^user_list/','chat.views.get_active_users',name='user_list'),
    url(r'^lobby/','chat.views.get_lobby',name='lobby'),
)


