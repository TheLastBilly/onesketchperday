from django.contrib import admin
from .models import *

class PostAdmin(admin.ModelAdmin):
    readonly_fields = ['timestamp', 'id', 'likes', 'date']

admin.site.register(User)
admin.site.register(Post, PostAdmin)
admin.site.register(Variable)
admin.site.register(MardownPost)