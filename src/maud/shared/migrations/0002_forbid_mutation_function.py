from django.db import migrations

from maud.shared.db import DROP_FORBID_MUTATION_FUNCTION, FORBID_MUTATION_FUNCTION


class Migration(migrations.Migration):
    dependencies = [("shared", "0001_initial")]

    operations = [migrations.RunSQL(FORBID_MUTATION_FUNCTION, DROP_FORBID_MUTATION_FUNCTION)]
