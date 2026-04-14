from functools import lru_cache

from django.db import connection

from .models import Owner


@lru_cache(maxsize=1)
def owner_has_complex_column():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select 1
            from information_schema.columns
            where table_schema = current_schema()
              and table_name = 'owner'
              and column_name = 'complex_id'
            """
        )
        return cursor.fetchone() is not None


def owner_queryset():
    queryset = Owner.objects.order_by('name')
    if not owner_has_complex_column():
        queryset = queryset.defer('complex')
    return queryset


def owners_for_complex(complex_id=None):
    queryset = owner_queryset()
    if complex_id is None:
        return queryset
    if owner_has_complex_column():
        return queryset.filter(complex_id=complex_id)
    return queryset


def owner_matches_complex(owner, complex_id):
    if owner is None or complex_id is None:
        return False
    if owner_has_complex_column():
        return owner.complex_id == complex_id
    return True
