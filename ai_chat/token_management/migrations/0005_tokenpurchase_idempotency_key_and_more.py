# Generated by Django 5.0.4 on 2025-03-16 16:22

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('token_management', '0004_alter_tokenusage_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='tokenpurchase',
            name='idempotency_key',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='tokenpurchase',
            name='is_processing',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tokenpurchase',
            name='transaction_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='usertokenlimit',
            name='token_reset_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='usertokenlimit',
            name='token_usage_this_month',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='tokenpurchase',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='usertokenlimit',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='token_limit', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='tokenpurchase',
            index=models.Index(fields=['user', 'payment_status'], name='token_manag_user_id_b216fb_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenpurchase',
            index=models.Index(fields=['transaction_id'], name='token_manag_transac_c73da1_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenpurchase',
            index=models.Index(fields=['idempotency_key'], name='token_manag_idempot_a0074f_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenusage',
            index=models.Index(fields=['user', 'timestamp'], name='token_manag_user_id_e380b8_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenusage',
            index=models.Index(fields=['feature'], name='token_manag_feature_fac636_idx'),
        ),
    ]
