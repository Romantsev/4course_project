import django.db.models.deletion
from django.db import migrations, models


def populate_owner_complex(apps, schema_editor):
    Owner = apps.get_model('complexes', 'Owner')
    Apartment = apps.get_model('complexes', 'Apartment')

    owner_complex_map = {}
    apartment_pairs = (
        Apartment.objects
        .filter(owner_id__isnull=False)
        .order_by('owner_id', 'entrance__building__complex_id')
        .values_list('owner_id', 'entrance__building__complex_id')
    )
    for owner_id, complex_id in apartment_pairs:
        if owner_id not in owner_complex_map and complex_id is not None:
            owner_complex_map[owner_id] = complex_id

    for owner_id, complex_id in owner_complex_map.items():
        Owner.objects.filter(owner_id=owner_id, complex_id__isnull=True).update(
            complex_id=complex_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ('complexes', '0010_alter_maintenancerequest_table_alter_visitor_table'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE owner "
                        "ADD COLUMN IF NOT EXISTS complex_id integer "
                        "REFERENCES residential_complex(complex_id) "
                        "DEFERRABLE INITIALLY DEFERRED"
                    ),
                    reverse_sql=(
                        "ALTER TABLE owner DROP COLUMN IF EXISTS complex_id"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='owner',
                    name='complex',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='complex_id',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='owners',
                        to='complexes.residentialcomplex',
                    ),
                ),
            ],
        ),
        migrations.RunPython(populate_owner_complex, migrations.RunPython.noop),
    ]
