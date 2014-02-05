from django.core.files.storage import FileSystemStorage
from django.db import models
from django.dispatch import receiver
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.template.defaultfilters import slugify
import zipfile
import os, errno
import glob
from subprocess import call


#for converter
from xlrd import open_workbook,cellname
from xlutils.copy import copy # http://pypi.python.org/pypi/xlutils
from xlwt import easyxf # http://pypi.python.org/pypi/xlwt
import sys
import csv
import time

class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name

class Affected(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(editable=False)
    original = models.FileField(storage=OverwriteStorage(),
                                upload_to='uploads', null=True, blank=True,
                                help_text="""Zip file with either geotiff and
                                        projection or shapefiles and friends""")
    # type = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False):
        slug = slugify(self.name)
        
        # Deletes an existing affected with the same slug name
        num_results = Affected.objects.filter(slug = slug).count()
        if num_results:
            l = Affected.objects.get(slug=slug)
            l.delete()

        self.slug = slug
        super(Affected, self).save(force_insert, force_update)

def create_folder(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

@receiver(models.signals.pre_save, sender=Affected)
def affected_handler(sender, instance, *args, **kwargs):
    """
    Post process the uploaded affected
    Convert 
    """

    instance.slug = slugify(instance.name)

    # Make a folder with the slug name
    # and create a 'raw' subdirectory to hold the files
    affected_folder = os.path.join(settings.MEDIA_ROOT, 'affecteds', instance.slug)
    create_folder(affected_folder)
    zip_out = os.path.join(affected_folder, 'converted')
    create_folder(zip_out)

    #This prints cell values on terminal
    #xlspath = os.path.join(settings.MEDIA_ROOT, 'uploads', instance.original.name)
    book = open_workbook(file_contents=instance.original.read())
    sheet = book.sheet_by_index(0)
    print sheet.name
    print sheet.nrows
    print sheet.ncols
    for row_index in range(sheet.nrows):
        for col_index in range(sheet.ncols):
            print cellname(row_index,col_index),'-',
            print sheet.cell(row_index,col_index).value

    #This writes the original xls file (first sheet for index 0) into a csv file.
    sheet = book.sheet_by_index(0)
    filename = instance.original.name + "_raw.csv"
    outname = os.path.join(zip_out, filename)

    fp = open((outname), 'wb')
    wr = csv.writer(fp, quoting=csv.QUOTE_ALL)
    for rownum in xrange(sheet.nrows):
         wr.writerow([unicode(val).encode('utf8') for val in sheet.row_values(rownum)])
    fp.close()

    # #To edit
    # #This rewrites a new csv file formatted according to proposed geocoded shapefile join table
    # filename2 = instance.original.name + "SHP.csv"
    # outname2 = open(os.path.join(zip_out, filename2), 'wb')    
    # with open(outname2, 'wb') as f:
    #      writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    #      writer.writerow( ('CALAMITYTYPE', 'REGION', 'PROVINCE', 'CITYMUNICIPALITY', 'NSCBCODE', 'AFFBGYS', 'AFFFAMILIES', 'AFFPERSONS', 'EVACCTRS', 'IEC_FAM', 'IEC_PERSONS', 'OEC_FAM', 'OEC_PERSONS', 'SERVED_FAMS', 'SERVED_PERSONS') )
    #      calamityname = raw_input("What type of calamity is this?")
    #      regCounter = 0
    #      provCounter = 1
    #      #removed 12 in xrange
    #      for rownum in xrange(sheet.nrows):
    #           region = 'region'
    #           province = 'province'

    #           #Selects only municipality entries based on cell alignment
    #           if len(sheet.cell(rownum, 2).value) > 0 and 'region' not in str(sheet.cell(rownum,1).value.encode('ascii', 'ignore')).lower():
    #                #Repeats 'region' values for empty cells
    #                while len(sheet.cell(rownum-regCounter,1).value)==0:
    #                     regCounter = regCounter +1
    #                region = str(sheet.cell(rownum-regCounter, 1).value).upper().replace('REGION','').strip()
    #                #Repeats 'province' values for empty cells
    #                #while book.xf_list[sheet.cell(rownum-provCounter,2).xf_index].alignment.hor_align != 1:
    #                #     provCounter = provCounter + 1
    #                #province = sheet.cell(rownum-provCounter, 2).value
    #                nums = []
    #                #Removes white spaces from cells with numerical values, replaces black cells with 0
    #                for colnum in [3, 4, 5]:
    #                     if len(str(sheet.cell(rownum, colnum).value).strip()) == 0:
    #                          nums.append(0)
    #                     else:
    #                          nums.append(int(float(str(sheet.cell(rownum, colnum).value).strip())))
    #                writer.writerow( (calamityname.upper(), region.upper(), province.upper(), sheet.cell(rownum,2).value.encode('ascii', 'ignore').upper(), nums[0], nums[1], nums[2] ))
    #                regCounter = 1
    #                provCounter = 1
    # f.close()
    # print 'Conversion Successful Honey!' 
