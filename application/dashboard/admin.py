from django.contrib import admin
from .models import Listing, Reaction
# Register your models here.

@admin.register(Listing)
class ListingRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_search_count', 'created_at')
    search_fields = ('id',)

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'reactiedatum', 'type', 'positie_is_definitief')
    search_fields = ('id', 'type')