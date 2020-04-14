import os, os.path, tempfile, zipfile
import shutil, traceback
from osgeo import ogr, osr
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.http import FileResponse
from django.contrib.gis.gdal import DataSource
from shapeEditor.shared.models import Shapefile
from shapeEditor.shared.models import Attribute
from shapeEditor.shared.models import Feature
from shapeEditor.shared import utils
from shapeEditor.shared.models import AttributeValue

def import_data(shapefile):
    fd,fname = tempfile.mkstemp(suffix=".zip")
    os.close(fd)

    f = open(fname, "wb")
    for chunk in shapefile.chunks():
        f.write(chunk)
    f.close()

    if not zipfile.is_zipfile(fname):
        os.remove(fname)
        return "Not a valid zip archive."

    zip = zipfile.ZipFile(fname)
    required_suffixes = [".shp", ".shx", ".dbf", ".prj"]
    has_suffix = {}

    for suffix in required_suffixes:
        has_suffix[suffix] = False

    for info in zip.infolist():
        suffix = os.path.splitext(info.filename)[1].lower()
        if suffix in required_suffixes:
            has_suffix[suffix] = True

    for suffix in required_suffixes:
        if not has_suffix[suffix]:
            zip.close()
            os.remove(fname)
            return "Archive missing required " + suffix + " file."
    
    shapefile_name = None
    dir_name = tempfile.mkdtemp()
    for info in zip.infolist():
        if (info.filename.endswith(".shp")==True):
            shapefile_name = info.filename   
        dst_file = os.path.join(dir_name, info.filename)
        f = open(dst_file, "wb")
        f.write(zip.read(info.filename))
        f.close()
    zip.close()

    try:
        datasource = ogr.Open(os.path.join(dir_name,shapefile_name))
        layer = datasource.GetLayer(0)
        ds = DataSource(os.path.join(dir_name,shapefile_name))
        lyr = ds[0]
        shapefile_ok = True
    except:
        traceback.print_exc()
        shapefile_ok = False
    if not shapefile_ok:
        os.remove(fname)
        shutil.rmtree(dir_name)
        return "Not a valid shapefile."

    src_spatial_ref = layer.GetSpatialRef()
    print(src_spatial_ref)
    geom_type = layer.GetLayerDefn().GetGeomType()
    geom_name = ogr.GeometryTypeToName(geom_type)
    shapefile = Shapefile(filename=shapefile_name,srs_wkt=src_spatial_ref.ExportToWkt(),geom_type=geom_name)
    shapefile.save()

    attributes = []
    layer_def = layer.GetLayerDefn()
    for i in range(layer_def.GetFieldCount()):
        field_def = layer_def.GetFieldDefn(i)
        attr = Attribute(shapefile=shapefile,name=field_def.GetName(),type=field_def.GetType(),width=field_def.GetWidth(),precision=field_def.GetPrecision())
        attr.save()
        attributes.append(attr)

    dst_spatial_ref = osr.SpatialReference()
    dst_spatial_ref.ImportFromEPSG(4326)
    coord_transform = osr.CoordinateTransformation(src_spatial_ref, dst_spatial_ref)

    for i in range(layer.GetFeatureCount()):
        src_feature = layer.GetFeature(i)
        src_geometry = src_feature.GetGeometryRef()
        # src_geometry.Transform(coord_transform)
        geometry = GEOSGeometry(src_geometry.ExportToWkt())
        geometry = utils.wrap_geos_geometry(geometry)       
        geom_field = utils.calc_geometry_field(geom_name)
        fields = {}
        fields['shapefile'] = shapefile
        fields['name'] = 'GAPA_NAPA'
        fields[geom_field] = geometry
        feature = Feature(**fields)
        feature.save()

    for attr in attributes:
        success,result = utils.get_ogr_feature_attribute(attr, src_feature)
        if not success:
            os.remove(fname)
            shutil.rmtree(dir_name)
            shapefile.delete()
            return result
        attr_value = AttributeValue(feature=feature,attribute=attr,value=result)
        attr_value.save()

    os.remove(fname)
    shutil.rmtree(dir_name, ignore_errors=True, onerror=None)
    return None

def export_data(shapefile):
    dst_dir = tempfile.mkdtemp()
    dst_file = os.path.join(dst_dir, shapefile.filename)
    dst_spatial_ref = osr.SpatialReference()
    dst_spatial_ref.ImportFromWkt(shapefile.srs_wkt)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.CreateDataSource(dst_file)
    layer = datasource.CreateLayer(shapefile.filename,dst_spatial_ref)
    for attr in shapefile.attribute_set.all():
        field = ogr.FieldDefn(attr.name, attr.type)
        field.SetWidth(attr.width)
        field.SetPrecision(attr.precision)
        layer.CreateField(field)  
    src_spatial_ref = osr.SpatialReference()
    src_spatial_ref.ImportFromEPSG(4326)
    coord_transform = osr.CoordinateTransformation(src_spatial_ref, dst_spatial_ref) 
    geom_field = utils.calc_geometry_field(shapefile.geom_type)  
    for feature in shapefile.feature_set.all():
        geometry = getattr(feature, geom_field)  
        geometry = utils.unwrap_geos_geometry(geometry)
        dst_geometry = ogr.CreateGeometryFromWkt(geometry.wkt)
        dst_geometry.Transform(coord_transform)
        dst_feature = ogr.Feature(layer.GetLayerDefn())
        dst_feature.SetGeometry(dst_geometry)
        for attr_value in feature.attributevalue_set.all():
            utils.set_ogr_feature_attribute(attr_value.attribute,attr_value.value,dst_feature)
        layer.CreateFeature(dst_feature)
    layer = None
    datasource = None
    temp = tempfile.TemporaryFile()
    zip = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)

    shapefile_name = os.path.splitext(shapefile.filename)[0]

    for fName in os.listdir(dst_dir):
        zip.write(os.path.join(dst_dir, fName), fName)
    zip.close()
    shutil.rmtree(dst_dir)
    temp.flush()
    temp.seek(0)
    response = FileResponse(temp)
    response['Content-type'] = "application/zip"
    response['Content-Disposition'] = "attachment; filename=" + shapefile_name + ".zip"
    return response

