from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('complexes', '0004_alter_storageroom_apartment_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
DO $$
BEGIN
  -- Ensure apartment_id column exists before altering nullability
  IF NOT EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_name = 'resident' AND column_name = 'apartment_id'
  ) THEN
    BEGIN
      ALTER TABLE resident
      ADD COLUMN apartment_id integer
      REFERENCES apartment(apartment_id)
      DEFERRABLE INITIALLY DEFERRED;
    EXCEPTION WHEN undefined_table THEN
      -- If resident or apartment tables don't exist yet, skip
      RETURN;
    END;
  END IF;

  -- Make the column nullable (if it exists)
  BEGIN
    ALTER TABLE resident ALTER COLUMN apartment_id DROP NOT NULL;
  EXCEPTION WHEN undefined_column THEN
    -- Column still doesn't exist – nothing to do
    NULL;
  END;
END $$;
""",
            reverse_sql="ALTER TABLE resident ALTER COLUMN apartment_id SET NOT NULL;",
        ),
    ]

