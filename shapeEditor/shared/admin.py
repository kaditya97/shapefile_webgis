from django.contrib import admin

# Register your models here.
from django.contrib.gis import admin
from shapeEditor.shared.models import *

admin.site.register(Shapefile, admin.ModelAdmin)
admin.site.register(Feature, admin.GeoModelAdmin)
admin.site.register(Attribute, admin.ModelAdmin)
admin.site.register(AttributeValue, admin.ModelAdmin)