from django_filters import rest_framework as filters
from .. import models
from .. import filters as custom_filters

class ProfileFilters(filters.FilterSet):

    name = custom_filters.CharFieldContainsFilter()
    class Meta:
        model = models.SC2Profile
        fields = ('id',)