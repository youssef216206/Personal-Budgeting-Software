# Generated manually for default categories

from django.db import migrations


def seed_categories(apps, schema_editor):
    Category = apps.get_model("budgeting", "Category")
    names = [
        "Food",
        "Transport",
        "Bills",
        "Entertainment",
        "Healthcare",
        "Salary",
        "Freelance",
        "Other",
    ]
    for name in names:
        Category.objects.get_or_create(name=name, user=None)


def unseed(apps, schema_editor):
    Category = apps.get_model("budgeting", "Category")
    Category.objects.filter(user__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("budgeting", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed),
    ]
