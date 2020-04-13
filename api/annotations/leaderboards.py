from decimal import Decimal

from django.db.models import F, DecimalField, Case, When
from django.db.models import QuerySet
from django.db.models.expressions import Window
from django.db.models.functions import Rank

from api.models import Leaderboard


def qs_with_ranking() -> QuerySet:
    rank_window = Window(expression=Rank(),
                         order_by=F('elo').desc())
    board = (
        Leaderboard
        .objects
        .select_related('toon')
        .order_by('-elo')
            .annotate(name=F("toon__name"))
            .annotate(losses=F("games") - F("wins"))
            .annotate(rank=rank_window)
            .annotate(win_rate=Case(
            When(games=0, then=0),
            default=(Decimal('1.0') * F("wins") / F("games")) * 100,
            output_field=DecimalField(),
        )
        )
    )
    return board
