from datetime import timedelta

from django.db import migrations


def fill_flag(apps, schema_editor):
    SepsisCase = apps.get_model('cases', 'SepsisCase')
    pending = []
    for case in SepsisCase.objects.iterator(chunk_size=500):
        if case.first_antibiotic_time is None:
            case.abx_within_3h = False
        else:
            gap = case.first_antibiotic_time - case.arrival_time
            case.abx_within_3h = gap <= timedelta(hours=3)
        pending.append(case)
        if len(pending) == 500:
            SepsisCase.objects.bulk_update(pending, ['abx_within_3h'])
            pending = []
    if pending:
        SepsisCase.objects.bulk_update(pending, ['abx_within_3h'])


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0002_add_abx_flag"),
    ]

    operations = [
        migrations.RunPython(fill_flag, migrations.RunPython.noop),
    ]
