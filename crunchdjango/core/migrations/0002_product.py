# Generated by Django 2.2.5 on 2019-09-19 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('goods_nm', models.CharField(max_length=200)),
                ('goods_no', models.IntegerField()),
                ('goods_price', models.IntegerField()),
                ('image_src', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'product',
            },
        ),
    ]
