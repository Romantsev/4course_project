from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffaccount',
            name='access_type',
            field=models.CharField(choices=[('guard', 'Guard'), ('maintenance', 'Maintenance')], default='maintenance', max_length=20),
        ),
    ]
