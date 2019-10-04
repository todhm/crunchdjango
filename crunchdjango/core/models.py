from django.db import models


class Task(models.Model):
    class Meta:
        db_table = 'task'
    nk = models.CharField(max_length=100,unique=True, db_index=True,primary_key=True)
    progress = models.IntegerField()
    name = models.CharField(max_length=200)
    identifier = models.CharField(max_length=200)
    complete = models.BooleanField(default=False)
    regDt = models.DateTimeField(auto_now_add=True)
    modDt = models.DateTimeField(auto_now=True)


class Product(models.Model):
    class Meta:
        db_table = 'product'
    goods_nm = models.CharField(max_length=200)
    goods_no = models.IntegerField()
    goods_price = models.IntegerField()
    image_src = models.CharField(max_length=200)
