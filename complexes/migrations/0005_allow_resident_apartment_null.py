from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('complexes', '0004_alter_storageroom_apartment_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE resident ALTER COLUMN apartment_id DROP NOT NULL;",
            reverse_sql="ALTER TABLE resident ALTER COLUMN apartment_id SET NOT NULL;",
        ),
    ]

