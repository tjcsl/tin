from django.contrib import admin

from .models import Container, ContainerPackage, ContainerTask

# Register your models here.

admin.site.register(Container)
admin.site.register(ContainerTask)
admin.site.register(ContainerPackage)
