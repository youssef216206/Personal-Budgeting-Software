# Default category for clothing / retail voice phrases

from django.db import migrations


def add_shopping(apps, schema_editor):
    Category = apps.get_model("budgeting", "Category")
    Category.objects.get_or_create(name="Shopping", user=None)


def remove_shopping(apps, schema_editor):
    Category = apps.get_model("budgeting", "Category")
    Category.objects.filter(name="Shopping", user__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("budgeting", "0006_subscription"),
    ]

    operations = [
        migrations.RunPython(add_shopping, remove_shopping),
    ]
