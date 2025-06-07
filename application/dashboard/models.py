from django.db import models
from django.utils import timezone


class Listing(models.Model):
    data = models.JSONField()
    total_search_count = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

class Reaction(models.Model):
    id = models.BigIntegerField(primary_key=True)  # from "id" in data
    obj_id = models.BigIntegerField()
    urlKey = models.CharField(max_length=100)
    closingDate = models.DateTimeField()
    publicationDate = models.DateTimeField()
    #"urlKey": "12081-vanembdenstraat-384-delft",
    #"closingDate": "2026-06-06 19:00:00",
    #"publicationDate": "2025-06-06 15:04:00",

    created_at = models.DateTimeField(default=timezone.now)
    kan_verwijderd_worden = models.BooleanField()
    toewijzing_id = models.BigIntegerField()
    reactiedatum = models.DateTimeField()
    type = models.CharField(max_length=32)
    positie_is_definitief = models.BooleanField()
    positie = models.IntegerField(null=True, blank=True)
    motivatie = models.TextField(null=True, blank=True)
    # Store the nested/extra data as JSON
    advertentie = models.JSONField(null=True, blank=True)
    object_data = models.JSONField(null=True, blank=True)
    huidige_aanbieding = models.JSONField(null=True, blank=True)
    #Huidige aanbieding
    reactiedatum =  models.DateTimeField()
    uitersteReactiedatum = models.DateTimeField(null=True, blank=True)
    #"reactiedatum": "2025-06-06 15:09:41", "reactiePositie": 0,
    #"uiterste Reactiedatum": "2025-06-09 16:00:00",

    persoonlijke_aanbieding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class Offer(models.Model):
    id = models.BigIntegerField(primary_key=True)
    url_key = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100, blank=True, null=True)
    house_number = models.CharField(max_length=20, blank=True, null=True)
    dwelling_type = models.CharField(max_length=50, blank=True, null=True)
    total_rent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    net_rent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    publication_date = models.DateTimeField(blank=True, null=True)
    closing_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    area_dwelling = models.FloatField(blank=True, null=True)
    available_from_date = models.DateField(blank=True, null=True)
    # Store the entire original JSON as backup, if you want flexibility:
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Offer {self.id} - {self.city} - {self.street} {self.house_number}"

    class Meta:
        verbose_name = "Offer"
        verbose_name_plural = "Offers"