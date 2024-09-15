from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_query_param = 'p'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params:
            page_size = request.query_params.get(self.page_size_query_param, self.page_size)
            page_size = min(int(page_size), self.max_page_size)  # Ensure page size does not exceed max limit
            self.page_size = page_size
        return super().paginate_queryset(queryset, request, view)