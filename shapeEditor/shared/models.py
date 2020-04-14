from django.contrib.gis.db import models

class Shapefile(models.Model):
    filename = models.CharField(max_length=255)
    srs_wkt = models.TextField()
    geom_type = models.CharField(max_length=50)
    def __str__(self):
        return self.filename

class Attribute(models.Model):
    shapefile = models.ForeignKey(Shapefile, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.IntegerField()
    width = models.IntegerField()
    precision = models.IntegerField()
    def __str__(self):
        return self.name

class Feature(models.Model):
    shapefile = models.ForeignKey(Shapefile, on_delete=models.CASCADE)
    name = models.CharField(max_length=255,blank=True, null=True)
    geom_point = models.PointField(srid=4326,blank=True, null=True)
    geom_multipoint = \
        models.MultiPointField(srid=4326,blank=True, null=True)
    geom_multilinestring = \
        models.MultiLineStringField(srid=4326,blank=True, null=True)
    geom_multipolygon = \
        models.MultiPolygonField(srid=4326,blank=True, null=True)
    geom_geometrycollection = \
        models.GeometryCollectionField(srid=4326,blank=True,null=True)
    def __str__(self):
        return str(self.shapefile)

class AttributeValue(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255,blank=True, null=True)
    def __str__(self):
        return self.value