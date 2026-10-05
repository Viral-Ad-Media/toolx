from django.contrib import admin

# Register your models here.
from .models import Question, Answer, InstantGenerator


# Register your models here.
class QuestionAdmin(admin.ModelAdmin):
    pass


class AnswerAdmin(admin.ModelAdmin):
    pass


class InstantGeneratorAdmin(admin.ModelAdmin):
    pass


admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(InstantGenerator, InstantGeneratorAdmin)



