from corpus.models import Recording, Sentence, QualityControl
from django.db.models import Sum, Count, When, Value, Case, IntegerField


def get_num_approved(query):
    query = query\
        .annotate(sum_approved=Sum(
            Case(
                When(
                    quality_control__isnull=True,
                    then=Value(0)),
                When(
                    quality_control__approved=True,
                    then=Value(1)),
                When(
                    quality_control__approved=False,
                    then=Value(0)),
                default=Value(0),
                output_field=IntegerField())))
    return query.sum_approved


def get_net_votes(query):
    query = query\
        .annotate(total_up_votes=Sum('quality_control__good'))\
        .annotate(total_down_votes=Sum('quality_control__good'))

    return (query.total_up_votes, query.total_down_votes)
