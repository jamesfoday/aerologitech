from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AffiliateOffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=140)),
                ('offer_type', models.CharField(choices=[('hotel', 'Hotel'), ('activity', 'Activity'), ('flight', 'Flight')], max_length=20)),
                ('region', models.CharField(max_length=80)),
                ('teaser', models.TextField()),
                ('provider', models.CharField(max_length=80)),
                ('affiliate_url', models.URLField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='explore/offers')),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['sort_order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('category', models.CharField(choices=[('activity', 'Activity'), ('historical', 'Historical'), ('nature', 'Nature'), ('culture', 'Culture'), ('market', 'Market'), ('beach', 'Beach')], max_length=20)),
                ('region', models.CharField(help_text='e.g. Banjul, Kololi, Jufureh', max_length=80)),
                ('short_desc', models.TextField()),
                ('hero_image', models.ImageField(blank=True, null=True, upload_to='explore/places')),
                ('map_url', models.URLField(blank=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('is_featured', models.BooleanField(default=True)),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ClickEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('referer', models.TextField(blank=True)),
                ('utm_source', models.CharField(blank=True, max_length=80)),
                ('utm_medium', models.CharField(blank=True, max_length=80)),
                ('utm_campaign', models.CharField(blank=True, max_length=120)),
                ('session_key', models.CharField(blank=True, max_length=120)),
                ('offer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clicks', to='explore.affiliateoffer')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

