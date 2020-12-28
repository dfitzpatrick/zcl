from rest_framework import viewsets, permissions

from . import queries, filters, serializers


class LeaderboardView(viewsets.ModelViewSet):
    serializer_class = serializers.LeaderboardSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    filterset_class = filters.LeaderboardFilter
    queryset = queries.leaderboard_queryset()