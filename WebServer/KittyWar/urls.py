from django.conf.urls import url

from . import views

app_name = 'kittywar'
urlpatterns = [

    url(r'^$',                  views.index_view,        name = 'index'),
    url(r'Kittywar/register/$', views.register_view,     name = 'register'),
    url(r'Kittywar/login/$',    views.login_view,        name = 'login'),
    url(r'Kittywar/logout/$',   views.logout_view,       name = 'logout'),
    url(r'Kittywar/home/$',     views.home_view,         name = 'home'),	
]


