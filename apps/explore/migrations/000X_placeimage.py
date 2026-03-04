from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("explore", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlaceImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="explore/places/gallery")),
                ("sort_order", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "place",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="explore.place"),
                ),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
    ]
