from django.db import migrations


SQL_UP = r"""
-- Redefine trigger function to also handle duplicate incoming IDs
CREATE OR REPLACE FUNCTION public.assign_smallest_free_id()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  col name := TG_ARGV[0];
  val_text text := to_jsonb(NEW)->>col;
  incoming_id bigint;
  needs_assign boolean := false;
  v_exists boolean := false;
  new_id bigint;
  tbl regclass := TG_TABLE_NAME::regclass;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF val_text IS NULL OR val_text = '' THEN
      needs_assign := true;
    ELSE
      incoming_id := val_text::bigint;
      -- Check if such id already exists (e.g., sequence out of sync)
      EXECUTE format('SELECT EXISTS(SELECT 1 FROM %s WHERE %I = $1)', tbl::text, col)
        INTO v_exists USING incoming_id;
      IF v_exists THEN
        needs_assign := true;
      END IF;
    END IF;

    IF needs_assign THEN
      new_id := public.next_smallest_free_id(tbl, col);
      NEW := jsonb_populate_record(NEW, jsonb_build_object(col, new_id));
    END IF;
  END IF;
  RETURN NEW;
END
$$;

-- Bring related sequences in sync with current max IDs to minimize duplicate defaults
DO $$
DECLARE
  rec record;
BEGIN
  FOR rec IN (
    SELECT 'residential_complex' AS t, 'complex_id' AS c UNION ALL
    SELECT 'building','building_id' UNION ALL
    SELECT 'entrance','entrance_id' UNION ALL
    SELECT 'owner','owner_id' UNION ALL
    SELECT 'apartment','apartment_id' UNION ALL
    SELECT 'resident','resident_id' UNION ALL
    SELECT 'staff','staff_id' UNION ALL
    SELECT 'parking_zone','parking_zone_id' UNION ALL
    SELECT 'parking_spot','spot_id' UNION ALL
    SELECT 'complexes_storageroom','id'
  ) LOOP
    BEGIN
      EXECUTE format(
        'SELECT setval(pg_get_serial_sequence(''%1$s'', ''%2$s''), GREATEST(COALESCE((SELECT MAX(%2$I) FROM %1$s), 1), 1))',
        rec.t, rec.c
      );
    EXCEPTION WHEN undefined_function OR undefined_table THEN
      -- Skip if table/sequence isn't serial-managed
      CONTINUE;
    END;
  END LOOP;
END $$;
"""


SQL_DOWN = r"""
-- No-op downgrade: keep the safer behavior
SELECT 1;
"""


class Migration(migrations.Migration):
    dependencies = [
        ('complexes', '0006_smallest_free_ids'),
    ]

    operations = [
        migrations.RunSQL(SQL_UP, SQL_DOWN),
    ]

