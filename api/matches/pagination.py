from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

# https://stackoverflow.com/questions/31740039/django-rest-framework-pagination-extremely-slow-count

class PageNumberPaginationWithoutCount(PageNumberPagination):
    # Set any other options you want here like page_size

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))