"""shapeEditor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.contrib.gis import admin
import shapeEditor.shapefiles.views
import shapeEditor.tms.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^$', shapeEditor.shapefiles.views.list_shapefiles),
    url(r'import/', shapeEditor.shapefiles.views.import_shapefile),
    url(r'^export/(?P<shapefile_id>\d+)$', shapeEditor.shapefiles.views.export_shapefile),
    url(r'^json/$', shapeEditor.shapefiles.views.export_json, name="json_data"),
    url(r'^tms/', include(shapeEditor.tms.urls)),
    url(r'^edit/(?P<shapefile_id>\d+)$', shapeEditor.shapefiles.views.edit_shapefile),
    url(r'^find_feature$', shapeEditor.shapefiles.views.find_feature),
    url(r'^edit_feature/(?P<shapefile_id>\d+)/(?P<feature_id>\d+)$', shapeEditor.shapefiles.views.edit_feature),
    url(r'^edit_feature/(?P<shapefile_id>\d+)$',shapeEditor.shapefiles.views.edit_feature),
    url(r'^delete_feature/(?P<shapefile_id>\d+)/(?P<feature_id>\d+)$',shapeEditor.shapefiles.views.delete_feature),
    url(r'^delete/(?P<shapefile_id>\d+)$',shapeEditor.shapefiles.views.delete_shapefile),
]


