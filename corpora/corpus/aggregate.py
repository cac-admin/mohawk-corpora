from corpus.models import Recording, Sentence, QualityControl
from django.db.models import Sum, Count, When, Value, Case, IntegerField


def get_num_approved(query):
    d = query\
        .aggregate(sum_approved=Sum(
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
    return d['sum_approved']


def get_net_votes(query):
    d1 = query\
        .aggregate(total_up_votes=Sum('quality_control__good'))
    d2 = query\
        .aggregate(total_down_votes=Sum('quality_control__bad'))

    return (d1['total_up_votes'], d2['total_down_votes'])
