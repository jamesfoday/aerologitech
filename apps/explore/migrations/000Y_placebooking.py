from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("explore", "000X_placeimage"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlaceBooking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=40)),
                ("travel_date", models.DateField()),
                ("travelers", models.PositiveIntegerField(default=1)),
                ("message", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("new", "New"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")], default="new", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("place", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookings", to="explore.place")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
