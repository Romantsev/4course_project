from django.db import migrations, models


SQL_UP = """
ALTER TABLE residential_complex
    ADD CONSTRAINT uniq_residential_complex_name_address
    UNIQUE (name, address);

ALTER TABLE building
    ADD CONSTRAINT uniq_building_complex_number
    UNIQUE (complex_id, number);

ALTER TABLE entrance
    ADD CONSTRAINT uniq_entrance_building_number
    UNIQUE (building_id, number);

ALTER TABLE apartment
    ADD CONSTRAINT uniq_apartment_entrance_number
    UNIQUE (entrance_id, number);

ALTER TABLE owner
    ADD CONSTRAINT uniq_owner_complex_name_phone
    UNIQUE NULLS NOT DISTINCT (complex_id, name, phone);

ALTER TABLE resident
    ADD CONSTRAINT uniq_resident_apartment_fullname_contact
    UNIQUE NULLS NOT DISTINCT (apartment_id, fullname, contact);

ALTER TABLE staff
    ADD CONSTRAINT uniq_staff_complex_fullname_contact
    UNIQUE NULLS NOT DISTINCT (complex_id, fullname, contact);

ALTER TABLE parking_zone
    ADD CONSTRAINT uniq_parking_zone_entrance
    UNIQUE (entrance_id);

ALTER TABLE parking_spot
    ADD CONSTRAINT uniq_parking_spot_zone_number
    UNIQUE (parking_zone_id, number);

ALTER TABLE storage_room
    ADD CONSTRAINT uniq_storage_room_number
    UNIQUE (number);
"""


SQL_DOWN = """
ALTER TABLE storage_room DROP CONSTRAINT IF EXISTS uniq_storage_room_number;
ALTER TABLE parking_spot DROP CONSTRAINT IF EXISTS uniq_parking_spot_zone_number;
ALTER TABLE parking_zone DROP CONSTRAINT IF EXISTS uniq_parking_zone_entrance;
ALTER TABLE staff DROP CONSTRAINT IF EXISTS uniq_staff_complex_fullname_contact;
ALTER TABLE resident DROP CONSTRAINT IF EXISTS uniq_resident_apartment_fullname_contact;
ALTER TABLE owner DROP CONSTRAINT IF EXISTS uniq_owner_complex_name_phone;
ALTER TABLE apartment DROP CONSTRAINT IF EXISTS uniq_apartment_entrance_number;
ALTER TABLE entrance DROP CONSTRAINT IF EXISTS uniq_entrance_building_number;
ALTER TABLE building DROP CONSTRAINT IF EXISTS uniq_building_complex_number;
ALTER TABLE residential_complex DROP CONSTRAINT IF EXISTS uniq_residential_complex_name_address;
"""


class Migration(migrations.Migration):
    dependencies = [
        ('complexes', '0011_owner_complex'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(SQL_UP, SQL_DOWN),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name='residentialcomplex',
                    constraint=models.UniqueConstraint(
                        fields=('name', 'address'),
                        name='uniq_residential_complex_name_address',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='building',
                    constraint=models.UniqueConstraint(
                        fields=('complex', 'number'),
                        name='uniq_building_complex_number',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='entrance',
                    constraint=models.UniqueConstraint(
                        fields=('building', 'number'),
                        name='uniq_entrance_building_number',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='apartment',
                    constraint=models.UniqueConstraint(
                        fields=('entrance', 'number'),
                        name='uniq_apartment_entrance_number',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='owner',
                    constraint=models.UniqueConstraint(
                        fields=('complex', 'name', 'phone'),
                        name='uniq_owner_complex_name_phone',
                        nulls_distinct=False,
                    ),
                ),
                migrations.AddConstraint(
                    model_name='resident',
                    constraint=models.UniqueConstraint(
                        fields=('apartment', 'fullname', 'contact'),
                        name='uniq_resident_apartment_fullname_contact',
                        nulls_distinct=False,
                    ),
                ),
                migrations.AddConstraint(
                    model_name='staff',
                    constraint=models.UniqueConstraint(
                        fields=('complex', 'fullname', 'contact'),
                        name='uniq_staff_complex_fullname_contact',
                        nulls_distinct=False,
                    ),
                ),
                migrations.AddConstraint(
                    model_name='parkingzone',
                    constraint=models.UniqueConstraint(
                        fields=('entrance',),
                        name='uniq_parking_zone_entrance',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='parkingspot',
                    constraint=models.UniqueConstraint(
                        fields=('parking_zone', 'number'),
                        name='uniq_parking_spot_zone_number',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='storageroom',
                    constraint=models.UniqueConstraint(
                        fields=('number',),
                        name='uniq_storage_room_number',
                    ),
                ),
            ],
        ),
    ]
