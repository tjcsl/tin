from django.contrib import admin
from .models import Container, ContainerTask, ContainerPackage

# Register your models here.

admin.site.register(Container)
admin.site.register(ContainerTask)
admin.site.register(ContainerPackage)
