from django.contrib import admin
from .models import InstantGenerator


# Register your models here.
class InstantGeneratorAdmin(admin.ModelAdmin):
    pass


admin.site.register(InstantGenerator, InstantGeneratorAdmin)



