from django.db import migrations


SQL_UP = r"""
-- Generic function to compute the smallest free positive integer id for a table/column.
CREATE OR REPLACE FUNCTION public.next_smallest_free_id(p_table regclass, p_col name)
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE
  new_id bigint;
  sql text;
BEGIN
  -- Prevent concurrent generators from choosing the same id (per table).
  PERFORM pg_advisory_xact_lock(hashtext(p_table::text));

  sql := format(
    'SELECT gs AS id\n'
    'FROM generate_series(1, (SELECT COALESCE(MAX(%1$I),0)+1 FROM %2$s)) gs\n'
    'LEFT JOIN %2$s t ON t.%1$I = gs\n'
    'WHERE t.%1$I IS NULL\n'
    'ORDER BY gs\n'
    'LIMIT 1',
     p_col, p_table::text
  );
  EXECUTE sql INTO new_id;
  IF new_id IS NULL THEN
    new_id := 1;
  END IF;
  RETURN new_id;
END
$$;

-- Trigger function that writes the smallest free id into the pk column if not provided.
CREATE OR REPLACE FUNCTION public.assign_smallest_free_id()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  col name := TG_ARGV[0];
  new_id bigint;
BEGIN
  IF TG_OP = 'INSERT' THEN
    -- If pk is NULL or empty, assign the smallest available id.
    IF (to_jsonb(NEW)->>col) IS NULL OR (to_jsonb(NEW)->>col) = '' THEN
      new_id := public.next_smallest_free_id(TG_TABLE_NAME::regclass, col);
      NEW := jsonb_populate_record(NEW, jsonb_build_object(col, new_id));
    END IF;
  END IF;
  RETURN NEW;
END
$$;

-- Helper to create trigger if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='residential_complex_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER residential_complex_smallest_id_trg\n'
         || 'BEFORE INSERT ON residential_complex\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''complex_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='building_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER building_smallest_id_trg BEFORE INSERT ON building\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''building_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='entrance_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER entrance_smallest_id_trg BEFORE INSERT ON entrance\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''entrance_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='owner_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER owner_smallest_id_trg BEFORE INSERT ON owner\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''owner_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='apartment_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER apartment_smallest_id_trg BEFORE INSERT ON apartment\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''apartment_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='resident_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER resident_smallest_id_trg BEFORE INSERT ON resident\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''resident_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='staff_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER staff_smallest_id_trg BEFORE INSERT ON staff\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''staff_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='parking_zone_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER parking_zone_smallest_id_trg BEFORE INSERT ON parking_zone\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''parking_zone_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='parking_spot_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER parking_spot_smallest_id_trg BEFORE INSERT ON parking_spot\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''spot_id'')';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='storage_room_smallest_id_trg') THEN
    EXECUTE 'CREATE TRIGGER storage_room_smallest_id_trg BEFORE INSERT ON storage_room\n'
         || 'FOR EACH ROW EXECUTE FUNCTION public.assign_smallest_free_id(''id'')';
  END IF;
END $$;
"""


SQL_DOWN = r"""
-- Drop triggers (if present)
DROP TRIGGER IF EXISTS residential_complex_smallest_id_trg ON residential_complex;
DROP TRIGGER IF EXISTS building_smallest_id_trg ON building;
DROP TRIGGER IF EXISTS entrance_smallest_id_trg ON entrance;
DROP TRIGGER IF EXISTS owner_smallest_id_trg ON owner;
DROP TRIGGER IF EXISTS apartment_smallest_id_trg ON apartment;
DROP TRIGGER IF EXISTS resident_smallest_id_trg ON resident;
DROP TRIGGER IF EXISTS staff_smallest_id_trg ON staff;
DROP TRIGGER IF EXISTS parking_zone_smallest_id_trg ON parking_zone;
DROP TRIGGER IF EXISTS parking_spot_smallest_id_trg ON parking_spot;
DROP TRIGGER IF EXISTS storage_room_smallest_id_trg ON storage_room;
-- Drop functions
DROP FUNCTION IF EXISTS public.assign_smallest_free_id() CASCADE;
DROP FUNCTION IF EXISTS public.next_smallest_free_id(regclass, name) CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ('complexes', '0005_allow_resident_apartment_null'),
    ]

    operations = [
        migrations.RunSQL(SQL_UP, SQL_DOWN),
    ]

