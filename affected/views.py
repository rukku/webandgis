from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from affected.models import Affected
from subprocess import call
import glob
import os
from django.contrib.auth.decorators import login_required

def index(request):
    affected = Affected.objects.all()
    context = { 'affected': affected }
    return render(request, 'affected/index.html', context)

def detail(request, affected_slug):
    affected = get_object_or_404(Affected, slug=affected_slug)
   
    dlpath = affected.original.url
    #get GeoJSON file
    affected_folder = os.path.join(settings.MEDIA_URL, 'affected', affected_slug)
    geometryJSON = os.path.join(affected_folder, 'raw', 'geometry.json') 
    context = { 'affected': affected } 
    context['download'] = dlpath
    context['geojson'] = geometryJSON 

    return render(request, 'affected/detail.html', context)

def get_affected_data(affected_name):
     affected = Affected.objects.get(name=affected_name)
     affected_path = os.path.join(settings.MEDIA_ROOT, 'affected', affected.slug, 'raw')
     os.chdir(affected_path)
     filename = glob.glob('*.shp')[0]
     affected_file = os.path.join(affected_path, filename)
     return read_affected(affected_file)

@login_required(redirect_field_name='next')
def calculate(request):
    """Calculates the buildings affected by flood.
    """

    output = os.path.join(settings.MEDIA_ROOT, 'affected', 'impact.json')

    buildings = get_affected_data('Buildings')
    flood = get_affected_data('Flood')

    # assign the required keywords for inasafe calculations
    buildings.keywords['category'] = 'exposure'
    buildings.keywords['subcategory'] = 'structure'
    flood.keywords['category'] = 'hazard'
    flood.keywords['subcategory'] = 'flood'

    impact_function = FloodBuildingImpactFunction
    
    # run analsis
    impact_file = calculate_impact(affected=[buildings, flood], impact_fcn=impact_function)


    call(['ogr2ogr', '-f', 'GeoJSON',
          output, impact_file.filename])

    impact_geojson = os.path.join(settings.MEDIA_URL, 'affected', 'impact.json')

    context = impact_file.keywords
    context['geojson'] = impact_geojson
    context['user'] = request.user

    return render(request, 'affected/calculate.html', context)
