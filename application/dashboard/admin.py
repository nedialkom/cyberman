from django.contrib import admin
from .models import Listing, Reaction, Offer
# Register your models here.

@admin.register(Listing)
class ListingRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_search_count', 'created_at')
    search_fields = ('id',)

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'created_at',
                    'publicationDate',
                    'reactiedatum',
                    'closingDate',
                    'uitersteReactiedatum',
                    'type',
                    'positie_is_definitief',
                    )
    search_fields = ('id', 'type')


# Register Offer model in the admin site
@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'city',
        'street',
        'house_number',
        'dwelling_type',
        'total_rent',
        'publication_date',
        'created_at'
    )
    search_fields = (
        'id',
        'city',
        'street',
        'dwelling_type'
    )


