from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("complexes", "0007_fix_smallest_free_id_duplicates"),
    ]

    operations = [
        migrations.AddField(
            model_name="building",
            name="complex",
            field=models.ForeignKey(
                db_column="complex_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="buildings",
                to="complexes.residentialcomplex",
            ),
        ),
        migrations.AddField(
            model_name="entrance",
            name="building",
            field=models.ForeignKey(
                db_column="building_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="entrances",
                to="complexes.building",
            ),
        ),
        migrations.AddField(
            model_name="apartment",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                db_column="owner_id",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="apartments",
                to="complexes.owner",
            ),
        ),
        migrations.AddField(
            model_name="apartment",
            name="entrance",
            field=models.ForeignKey(
                db_column="entrance_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="apartments",
                to="complexes.entrance",
            ),
        ),
        migrations.AddField(
            model_name="parkingzone",
            name="entrance",
            field=models.ForeignKey(
                db_column="entrance_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="parking_zones",
                to="complexes.entrance",
            ),
        ),
        migrations.AddField(
            model_name="parkingspot",
            name="parking_zone",
            field=models.ForeignKey(
                db_column="parking_zone_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="spots",
                to="complexes.parkingzone",
            ),
        ),
        migrations.AddField(
            model_name="parkingspot",
            name="owner",
            field=models.ForeignKey(
                db_column="owner_id",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="parking_spots",
                to="complexes.owner",
            ),
        ),
        migrations.AddField(
            model_name="staff",
            name="complex",
            field=models.ForeignKey(
                db_column="complex_id",
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="staff",
                to="complexes.residentialcomplex",
            ),
        ),
    ]

