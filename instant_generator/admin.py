from django.contrib import admin
from .models import InstantGenerator, Profile


# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    pass


class InstantGeneratorAdmin(admin.ModelAdmin):
    pass


admin.site.register(Profile, ProfileAdmin)
admin.site.register(InstantGenerator, InstantGeneratorAdmin)


