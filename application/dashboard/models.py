from django.db import models
from django.utils import timezone


class Listing(models.Model):
    data = models.JSONField()
    total_search_count = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

class Reaction(models.Model):
    id = models.BigIntegerField(primary_key=True)  # from "id" in data
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
    persoonlijke_aanbieding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    #data = models.JSONField()  # Store the full item as JSON