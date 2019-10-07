import os
import logging
import json
import boto3
from django.shortcuts import render
from rest_framework import generics, permissions, status, views, viewsets
from core.models import Task, Product
from core.messages import INVALID_TRANSACTION,PERSONALIZE_ADD_ERROR,PERSONALIZE_GET_MODEL_ERROR
from django.db.models import Q
from celery.result import AsyncResult
from rest_framework.response import Response
from pymongo import MongoClient
from django.conf import settings
from utils.task_utils import launch_task
from utils.aws_utils import add_recommendation_data,get_recommendation_goods
from . import serializers

logger = logging.getLogger(__name__)

# Create your views here.


class BasicWorkerApi(views.APIView):
    def make_rsp(self, response):
        if response.status_code == status.HTTP_200_OK:
            if not response.data:
                response.data = {}
                response.data['result'] = 'success'
            if type(response.data) != dict:
                response.data = {'result': "success", 'data': response.data}
        return Response

    def launch_async_task(self, task_name, *args, identifier=False, **kwargs):
        data = {}
        try:
            result = launch_task(
                task_name,
                *args,
                **kwargs
            )
        except Exception as e:
            data['errorMessage'] = str(e)
            return self.make_rsp(Response(data, status=status.HTTP_400_BAD_REQUEST))
        try:
            if identifier:
                task = Task(nk=result.id, name=task_name,
                            progress=0, identifier=identifier)
            else:
                task = Task(nk=result.id, name=task_name, progress=0)
            task.save()
        except Exception as e:
            data['errorMessage'] = str(e)
            logger.error(INVALID_TRANSACTION, extra=data)
            return self.make_rsp(Response(data, status=status.HTTP_400_BAD_REQUEST))

        data['taskId'] = task.nk
        data['result'] = 'success'
        return self.make_rsp(Response(data, status=status.HTTP_200_OK))


# Create your views here.
class TestView(views.APIView):
    def get(self, response):
        url = os.environ.get("MONGO_URI")
        client = MongoClient(url)
        if settings.TESTING:
            db_name = 'test_db'
        else:
            db_name = 'crunchprice'

        table = client[db_name].goods_search_table.find(
            {}, {"_id": False}).limit(20)
        data = list(table)
        return Response(data)

    def post(self, request):
        data = request.data

        url = os.environ.get("MONGO_URI")
        client = MongoClient(url)

        if settings.TESTING:
            db_name = 'test_db'
        else:
            db_name = 'crunchprice'

        if type(data) == list:
            result = client[db_name].goods_search_table.insert_many(data)
            return Response(str(result.inserted_ids), status=status.HTTP_201_CREATED)
        elif type(data) == dict:
            result = client[db_name].goods_search_table.insert_one(data)
            return Response(str(result), status=status.HTTP_201_CREATED)
        else:
            data['errorMessage'] = 'error'
            logger.error(INVALID_TRANSACTION, extra=data)
            return self.make_rsp(Response(data, status=status.HTTP_400_BAD_REQUEST))

        # return Response(client[db_name].goods_search_table.find({}).count())
        # return Response(result)

    # def __init__(*args,**kwargs):
    #     super().__init__(*args,**kwargs):
    #     url  = os.environ.get("MONGO_URI")
    #     self.client = MongoClient(url)
    #     if settings.TESTING:
    #         self.db_name = 'test_db'
    #     else:
    #         self.db_name = 'crunchprice'


class GetTaskView(viewsets.ReadOnlyModelViewSet):
    lookup_url_kwarg = "nk"
    queryset = Task.objects.all()
    serializer_class = serializers.TaskSerializer

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task)
        task_id = serializer.data.get('nk')
        res = AsyncResult(task_id)
        status = res.state
        data = serializer.data
        data['status'] = status
        if status == "SUCCESS":
            data['result'] = "finished"
        elif status == "FAILURE":
            data['result'] = "failed"
        else:
            data['result'] = "running"
        if data['result'] == "failed" or data['result'] == "finished":
            task.complete = True
            task.progress = 100
            task.save()
            data['complete'] = True
            data['progress'] = 100
            data['data'] = res.result

        print('GetTaskView')
        return Response(data)


class ProductView(views.APIView):
    def get(self, request, *args, **kwargs):
        url = os.environ.get("MONGO_URI")
        client = MongoClient(url)
        goodsNo = kwargs.get('goodsNo')
        if settings.TESTING:
            db_name = 'test_db'
        else:
            db_name = 'crunchprice'

        table = client[db_name].goods_search_table.find(
            {'goodsNo': goodsNo}, {"_id": False})
        data = list(table)
        return Response(data)


class CategoryView(views.APIView):
    def get(self, request, *args, **kwargs):
        url = os.environ.get("MONGO_URI")
        client = MongoClient(url)
        cateCdRegex = "^"+kwargs.get('cateCd')[:3]

        if settings.TESTING:
            db_name = 'test_db'
        else:
            db_name = 'crunchprice'

        # table = client[db_name].goods_search_table.find(
        #     {"cateCd": {"$regex": cateCdRegex}}, {"_id": False}).limit(10)

        table = client[db_name].goods_search_table.aggregate(
            [
                {"$match": {"cateCd": {"$regex": cateCdRegex}}},
                {"$project": {"_id": 0, "goodsNo": 1, "goodsNm": 1, "imageSrc": 1, "goodsIconList": 1,
                              "minPrice": '$goodsUnitPrice10', "maxPrice": '$goodsUnitPrice1'}}
            ]
        )

        data = list(table)

        # for item in data:
        #     logger.error(item)
        # item['minPrice'] = item.pop('goodsUnitPrice10')
        # item['maxPrice'] = item.pop('goodsUnitPrice1')

        return Response(data)


class PersonalizeView(views.APIView):

    def post(self, request):
        url = os.environ.get("MONGO_URI")
        client = MongoClient(url)
        db_name =  settings.MONGODB_NAME
        data = request.data
        serializer_class = serializers.UserdataSerializer(data=data)
        if serializer_class.is_valid(raise_exception=True):
            validated_data = serializer_class.validated_data
            if validated_data.get("ORIGINAL_USER_ID"):
                original_user_id = validated_data['ORIGINAL_USER_ID']
                client[db_name].personalize_table.insert_one(validated_data)
                client[db_name].personalize_table.update_many({"USER_ID": original_user_id}, {
                                                            "$set": {"USER_ID": validated_data['USER_ID']}}, upsert=False)

            else:
                client[db_name].personalize_table.insert_one(validated_data) 
        #     AMAZON PERSONALIZE
        #     if not settings.TESTING and os.environ.get("PERSONALIZE_ACCESS_KEY") \
        #         and os.environ.get("PERSONALIZE_SECRET_KEY") and os.environ.get("PERSONALIZE_TRACKING_ID"):
        #         personalize_key = os.environ['PERSONALIZE_ACCESS_KEY']
        #         personalize_secret = os.environ['PERSONALIZE_SECRET_KEY']
        #         tracking_id = os.environ['PERSONALIZE_TRACKING_ID']
        #         personalize_client = boto3.client(
        #             'personalize-events',
        #             aws_access_key_id=personalize_key,
        #             aws_secret_access_key=personalize_secret,
        #             region_name='us-east-1'
        #         )
        #         try:
        #             result = add_recommendation_data(personalize_client,validated_data,tracking_id)
        #         except:
        #             return Response(PERSONALIZE_ADD_ERROR, status=status.HTTP_400_BAD_REQUEST)
        data = {}
        data['result'] = 'success'
        return Response(data, status=status.HTTP_201_CREATED)



class GetRecommendGoodsView(views.APIView):

    def get(self, request,**kwargs):
        url = os.environ.get("MONGO_URI")
        client = MongoClient(url)
        db_name =  settings.MONGODB_NAME
        user_id = self.kwargs.get("user_id")
        item_id = self.kwargs.get("item_id",'')
        

        if not settings.TESTING and os.environ.get("PERSONALIZE_ACCESS_KEY") \
            and os.environ.get("PERSONALIZE_SECRET_KEY") and os.environ.get("PERSONALIZE_CAMPAIGN_MODEL"):
            personalize_key = os.environ['PERSONALIZE_ACCESS_KEY']
            personalize_secret = os.environ['PERSONALIZE_SECRET_KEY']
            campaign_model = os.environ['PERSONALIZE_ITEM_BASED_MODEL'] if item_id else os.environ['PERSONALIZE_CAMPAIGN_MODEL']
            personalize_client = boto3.client(
                'personalize-runtime',
                aws_access_key_id=personalize_key,
                aws_secret_access_key=personalize_secret,
                region_name='us-east-1'
            )
            try:
                item_id_list = get_recommendation_goods(personalize_client,user_id,campaign_model,item_id=item_id)
            except Exception as e:
                return Response(PERSONALIZE_GET_MODEL_ERROR+str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            item_id_list = list(client[db_name].goods_search_table.find({},{'goodsNo':1}).limit(10))
            item_id_list = [ x['goodsNo'] for x in item_id_list]

        if item_id_list:
            results = client[db_name].goods_search_table.aggregate(
                [
                    {"$match": {"goodsNo": {"$in":item_id_list}}},
                    {"$project": {"_id": 0, "goodsNo": 1, "goodsNm": 1, "imageSrc": 1, "goodsIconList": 1,
                                    "minPrice": '$goodsUnitPrice10', "maxPrice": '$goodsUnitPrice1'}}
                ]
            )
            results = list(results)
        else:
            results = []
    
        return Response(results)



class AddUserView(views.APIView):

    def post(self, request):
        url = os.environ.get("MONGO_URI")
        client = MongoClient(url)
        db_name =  settings.MONGODB_NAME
        data = request.data
        serializer_class = serializers.UserdataSerializer(data=data)
        if serializer_class.is_valid(raise_exception=True):
            validated_data = serializer_class.validated_data
            if validated_data.get("ORIGINAL_USER_ID"):
                original_user_id = validated_data['ORIGINAL_USER_ID']
                client[db_name].personalize_table.insert_one(validated_data)
                client[db_name].personalize_table.update_many({"USER_ID": original_user_id}, {
                                                            "$set": {"USER_ID": validated_data['USER_ID']}}, upsert=False)

            else:
                client[db_name].personalize_table.insert_one(validated_data)
        data = {}
        data['result'] = 'success'
        return Response(data, status=status.HTTP_201_CREATED)
