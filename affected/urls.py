from django.conf.urls import patterns, url
from affected import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
      url(r'^(?P<affected_slug>[\w\-]+)/$', views.detail, name='detail'),
)
