from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("budgeting", "0004_alter_notification_type"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=("name", "user"),
                name="uniq_category_name_per_user",
            ),
        ),
    ]
