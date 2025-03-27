from django.contrib import admin
from .models import UploadedFile, WordStat

admin.site.register(UploadedFile)
admin.site.register(WordStat)
