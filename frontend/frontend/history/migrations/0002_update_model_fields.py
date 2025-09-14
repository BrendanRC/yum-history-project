from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='yumhistory',
            name='date_time',
        ),
        migrations.RemoveField(
            model_name='yumhistory',
            name='user',
        ),
        migrations.RemoveField(
            model_name='yumhistory',
            name='version',
        ),
        migrations.AddField(
            model_name='yumhistory',
            name='command',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='yumhistory',
            name='package_arch',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='yumhistory',
            name='package_version',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='yumhistory',
            name='timestamp',
            field=models.DateTimeField(default='2025-01-01 00:00:00'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='yumhistory',
            name='action',
            field=models.IntegerField(),
        ),
    ]
