from django.http import HttpResponse
from django.shortcuts import render
from shapeEditor.shared.models import Shapefile, Feature
from django.http import HttpResponseRedirect
from shapeEditor.shapefiles.forms import ImportShapefileForm
# from django.shortcuts import render_to_response
from shapeEditor.shapefiles import shapefileIO
from django.http import Http404
import traceback
from django.contrib.gis.geos import Point
from shapeEditor.shared.models import Feature
from shapeEditor.shared import utils
from django.contrib.gis import forms
from django.core.serializers import serialize

def list_shapefiles (request):
    shapefiles = Shapefile.objects.all().order_by('filename')
    return render(request, "list_shapefiles.html",{'shapefiles' : shapefiles})

def import_shapefile(request):
    if request.method == "GET":
        form = ImportShapefileForm()
        return render(request, "import_shapefile.html",{'form' : form, 'errMsg' : None})

    elif request.method == "POST":
        errMsg = None # initially.
        form = ImportShapefileForm(request.POST, request.FILES)
        if form.is_valid():
            shapefile = request.FILES['import_file']
            errMsg = shapefileIO.import_data(shapefile)
            if errMsg == None:
                return HttpResponseRedirect("/")
        return render(request, "import_shapefile.html",{'form' : form,'errMsg' : errMsg})

def export_shapefile(request, shapefile_id):
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)

    except Shapefile.DoesNotExist:
        raise Http404("No such shapefile")

    return shapefileIO.export_data(shapefile)

def export_json(request):
    try:
        # shapefile = Shapefile.objects.get(id=shapefile_id)
        shapefile = serialize("geojson", Feature.objects.all(), geometry_field='geom_multipolygon')

    except Shapefile.DoesNotExist:
        raise Http404("No such shapefile")
    return HttpResponse(shapefile, content_type='json')


def edit_shapefile(request, shapefile_id):
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)
    except Shapefile.DoesNotExist:
        return HttpResponseNotFound()
    tms_url = "http://" + request.get_host() + "/tms/"
    find_feature_url = "http://" + request.get_host() + "/editor/find_feature"
    add_feature_url = "http://" + request.get_host() + "/edit_feature/" + str(shapefile_id)
    return render(request, "select_feature.html", {'shapefile' : shapefile, 'find_feature_url' : find_feature_url,'add_feature_url' : add_feature_url, 'tms_url' : tms_url})

def find_feature(request):
    try:
        shapefile_id = int(request.GET['shapefile_id'])
        latitude = float(request.GET['latitude'])
        longitude = float(request.GET['longitude'])
        shapefile = Shapefile.objects.get(id=shapefile_id)
        pt = Point(longitude, latitude)
        radius = utils.calc_search_radius(latitude, longitude, 100)
        if shapefile.geom_type == "Point":
            query = Feature.objects.filter(geom_point__dwithin=(pt, radius))
        elif shapefile.geom_type in ["LineString", "MultiLineString"]:
            query = Feature.objects.filter(geom_multilinestring__dwithin=(pt, radius))
        elif shapefile.geom_type in ["Polygon", "MultiPolygon"]:
            query = Feature.objects.filter(geom_multipolygon__dwithin=(pt, radius))
        elif shapefile.geom_type == "MultiPoint":
            query = Feature.objects.filter(geom_multipoint__dwithin=(pt, radius))
        elif shapefile.geom_type == "GeometryCollection":
            query = feature.objects.filter(geom_geometrycollection__dwithin=(pt, radius))
        else:
            print( "Unsupported geometry: " + shapefile.geom_type)
            return HttpResponse("")
        if query.count() != 1:
            return HttpResponse("")
        feature = query[0]
        return HttpResponse("/edit_feature/" +str(shapefile_id)+"/"+str(feature.id))
    except:
        traceback.print_exc()
        return HttpResponse("")

def edit_feature(request, shapefile_id, feature_id=None):
    if request.method == "POST" and "delete" in request.POST:
        return HttpResponseRedirect("/delete_feature/" + shapefile_id+"/"+feature_id)
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)
    except ShapeFile.DoesNotExist:   
        return HttpResponseNotFound()

    if feature_id == None:
        feature = Feature(shapefile=shapefile)
    else:
        try:
            feature = Feature.objects.get(id=feature_id)
        except Feature.DoesNotExist:
            return HttpResponseNotFound()
    attributes = []
    for attr_value in feature.attributevalue_set.all():
        attributes.append([attr_value.attribute.name,attr_value.value])
        attributes.sort()
    if request.method == "GET":
        form = MyForm()
        return render(request, "template.html",{'form' : form})
    elif request.method == "POST":
        form = MyForm(request.POST)
        if form.is_valid():
        # Extract and save the form's contents here...
            return HttpResponseRedirect("/somewhere/else")
        return render(request, "template.html",{'form' : form})
    geometry_field = utils.calc_geometry_field(shapefile.geom_type)
    form_class = utils.get_map_form(shapefile)
    if request.method == "GET":
        wkt = getattr(feature, geometry_field)
        form = form_class({'geometry' : wkt})
        return render(request, "edit_feature.html",{'shapefile' : shapefile,'form' : form,'attributes' : attributes})
    elif request.method == "POST":
        form = form_class(request.POST)
        try:
            if form.is_valid():
                wkt = form.cleaned_data['geometry']
                setattr(feature, geometry_field, wkt)
                feature.save()
                return HttpResponseRedirect("/edit/" + shapefile_id)
        except ValueError:
            pass
        return render(request, "edit_feature.html",{'shapefile' : shapefile,'form' : form,'attributes' : attributes})

def delete_feature(request, shapefile_id, feature_id):
    try:
        feature = Feature.objects.get(id=feature_id)
    except Feature.DoesNotExist:
        return HttpResponseNotFound()
    if request.method == "POST":
        if request.POST['confirm'] == "1":
            feature.delete()
        return HttpResponseRedirect("/edit/" +shapefile_id)
    return render(request, "delete_feature.html")

def delete_shapefile(request, shapefile_id):
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)
    except Shapefile.DoesNotExist:
        return HttpResponseNotFound()
    if request.method == "GET":
        return render(request, "delete_shapefile.html",{'shapefile' : shapefile})
    elif request.method == "POST":
        if request.POST['confirm'] == "1":
            shapefile.delete()
        return HttpResponseRedirect("/")