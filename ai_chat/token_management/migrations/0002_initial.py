# Generated by Django 5.0.4 on 2025-03-15 18:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('token_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='tokenalert',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='token_alerts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tokenpurchase',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='token_purchases', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tokenusage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='token_usage', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='usertokenlimit',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='token_usage_limit', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='tokenalert',
            unique_together={('user', 'threshold', 'month', 'year')},
        ),
    ]
