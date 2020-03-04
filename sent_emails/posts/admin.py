from django.contrib import admin

from .models import Post, Group, Comment

# Register your models here.


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group",)
    search_fields = ("text", "group__title",)
    list_filter = ("pub_date",)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):

    list_display = ("pk", "title", "description", "slug",)
    search_fields = ("title", "description",)
    empty_value_display = '-пусто-'


# при регистрации модели Post источником конфигурации для неё назначаем класс PostAdmin
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment)
