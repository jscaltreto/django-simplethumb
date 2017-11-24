from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^(?P<basename>.*)\.(?P<encoded_spec>[\w\-_]+)\.(?P<ext>\w{3,4})/?$',
        views.serve_image,
        name="simplethumb"),
]
