from rest_framework import serializers
from core.models import Task, Product


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('nk','complete','progress')

# class ProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = ('goods_nm')


class UserdataSerializer(serializers.Serializer):
    TIMESTAMP = serializers.IntegerField() 
    EVENT_TYPE= serializers.ChoiceField(choices=[
        ('Click','Click'),
        ('Search','Search'),
        ('AddToCart','AddToCart'),
        ('RemoveFromCart','RemoveFromCart'),
        ('Checkout','Checkout'),
        ('Like','Like'),
        ('Comment','Comment'),
        ('Rating','Rating'),
        ('Play','Play'),
        ('Pause','Pause'),
        ('Resume','Resume'),
    ]) 
    ITEM_ID = serializers.IntegerField()
    USER_ID = serializers.CharField(trim_whitespace=True)
    ORIGINAL_USER_ID = serializers.CharField(required=False,allow_null=True,allow_blank=True,trim_whitespace=True)


