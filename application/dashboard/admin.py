from django.contrib import admin
from .models import Listing, Reaction, Offer
# Register your models here.

@admin.register(Listing)
class ListingRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_search_count', 'created_at')
    search_fields = ('id',)

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):

    def get_advertentie_status(self, obj):
        return obj.advertentie.get('status') if obj.advertentie else None
    get_advertentie_status.short_description = 'Advertentie Status'

    def get_object_city(self, obj):
        return obj.object_data.get('city', {}).get('name') if obj.object_data else None
    get_object_city.short_description = 'City'

    def get_object_street(self, obj):
        return obj.object_data.get('street') if obj.object_data else None
    get_object_street.short_description = 'Street'

    def get_object_house_number(self, obj):
        return obj.object_data.get('houseNumber') if obj.object_data else None
    get_object_house_number.short_description = 'House Number'

    def get_object_floor_id(self, obj):
        floor = obj.object_data.get('floor') if obj.object_data else None
        return floor.get('id') if floor else None
    get_object_floor_id.short_description = 'Floor ID'

    def get_object_total_rent(self, obj):
        return obj.object_data.get('totalRent') if obj.object_data else None
    get_object_total_rent.short_description = 'Total Rent'

    list_display = ('id',
                    'obj_id',
                    'get_advertentie_status',
                    'get_object_city',
                    'get_object_street',
                    'get_object_house_number',
                    'get_object_floor_id',
                    'get_object_total_rent',
                    'publicationDate',
                    'reactiedatum',
                    'created_at',
                    )

    search_fields = (
        'id',
        'type',
        'object_data.houseNumber',
    )


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'city',
        'street',
        'house_number',
        'dwelling_type',
        'total_rent',
        'net_rent',
        'area_dwelling',
        'publication_date',
        'created_at'
    )
    search_fields = (
        'id',
        'city',
        'street',
        'dwelling_type'
    )


