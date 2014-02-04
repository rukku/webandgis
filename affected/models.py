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
 
