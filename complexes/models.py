from django.db import models
from django.conf import settings

class ResidentialComplex(models.Model):
    complex_id = models.AutoField(primary_key=True)
    name = models.TextField()
    address = models.TextField()
    management = models.TextField(blank=True, null=True)
    contact = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'residential_complex'
        ordering = ['name']

    def __str__(self):
        return self.name


class Building(models.Model):
    building_id = models.AutoField(primary_key=True)
    number = models.IntegerField()
    floors = models.IntegerField()
    complex = models.ForeignKey(
        ResidentialComplex,
        on_delete=models.CASCADE,
        db_column='complex_id',
        related_name='buildings'
    )

    class Meta:
        managed = False
        db_table = 'building'
        ordering = ['number']

    def __str__(self):
        return f"Будинок {self.number} ({self.complex.name})"


class Entrance(models.Model):
    entrance_id = models.AutoField(primary_key=True)
    number = models.IntegerField()
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        db_column='building_id',
        related_name='entrances'
    )

    class Meta:
        managed = False
        db_table = 'entrance'
        ordering = ['number']

    def __str__(self):
        return f"Під'їзд {self.number}, буд. {self.building.number}"


class Owner(models.Model):
    owner_id = models.AutoField(primary_key=True)
    name = models.TextField()
    phone = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'owner'
        ordering = ['name']

    def __str__(self):
        return self.name


class Apartment(models.Model):
    apartment_id = models.AutoField(primary_key=True)
    number = models.IntegerField()
    floor = models.IntegerField()
    rooms = models.IntegerField()
    area_m2 = models.IntegerField(blank=True, null=True)
    owner = models.ForeignKey(
        Owner,
        on_delete=models.RESTRICT,
        db_column='owner_id',
        related_name='apartments',
        blank=True,
        null=True,         
    )
    entrance = models.ForeignKey(
        Entrance,
        on_delete=models.CASCADE,
        db_column='entrance_id',
        related_name='apartments'
    )

    class Meta:
        managed = False
        db_table = 'apartment'
        ordering = ['entrance', 'floor', 'number']

    def __str__(self):
        return f"Кв. {self.number} ({self.entrance})"



class Resident(models.Model):
    resident_id = models.AutoField(primary_key=True)
    fullname = models.TextField()
    contact = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        db_column='apartment_id',
        related_name='residents',
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = 'resident'
        ordering = ['fullname']

    def __str__(self):
        return self.fullname


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    fullname = models.TextField()
    contact = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    work_schedule = models.TextField(blank=True, null=True)
    complex = models.ForeignKey(
        ResidentialComplex,
        on_delete=models.CASCADE,
        db_column='complex_id',
        related_name='staff'
    )

    class Meta:
        managed = False
        db_table = 'staff'
        ordering = ['fullname']

    def __str__(self):
        return self.fullname


class ParkingZone(models.Model):
    parking_zone_id = models.AutoField(primary_key=True)
    type = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    entrance = models.ForeignKey(
        Entrance,
        on_delete=models.CASCADE,
        db_column='entrance_id',
        related_name='parking_zones'
    )

    class Meta:
        managed = False
        db_table = 'parking_zone'

    def __str__(self):
        return f"Паркінг зона {self.parking_zone_id} ({self.type})"


class ParkingSpot(models.Model):
    spot_id = models.AutoField(primary_key=True)
    number = models.IntegerField()
    status = models.TextField(blank=True, null=True)
    parking_zone = models.ForeignKey(
        ParkingZone,
        on_delete=models.CASCADE,
        db_column='parking_zone_id',
        related_name='spots'
    )
    owner = models.ForeignKey(
        Owner,
        on_delete=models.RESTRICT,
        db_column='owner_id',
        related_name='parking_spots'
    )

    class Meta:
        managed = False
        db_table = 'parking_spot'

    def __str__(self):
        return f"Місце {self.number} ({self.parking_zone})"


class StorageRoom(models.Model):
    STATUS_CHOICES = [
        ('free', 'Вільна'),
        ('occupied', 'Зайнята'),
        
    ]

    number = models.CharField(max_length=20)
    location = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='free')
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='storage_rooms',
        db_column='apartment_id',
    )

    class Meta:
        managed = False
        db_table = 'storage_room'

    def __str__(self):
        base = f"Комірка {self.number}"
        if self.apartment:
            return f"{base} (кв. {self.apartment.number})"
        return base




class Visitor(models.Model):
    fullname = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    apartment = models.ForeignKey(
        Apartment, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='visitors'
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='added_visitors'
    )

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Нова'),
        ('in_progress', 'В роботі'),
        ('done', 'Виконано'),
    ]

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='tickets')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='tickets')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
