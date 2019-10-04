from django.test import tag
from rest_framework.test import APIClient
from django.test import TestCase 
from django.urls import reverse
from pymongo import MongoClient 
import boto3
from utils.aws_utils import add_recommendation_data,get_recommendation_goods
from botocore.stub import Stubber
import os 

def create_user_data(**params):
    defaults = {
        'USER_ID':'1',
        'ITEM_ID':1001,
        'TIMESTAMP':1112,
        'EVENT_TYPE':'Click'
    }
    defaults.update(params)
    return defaults

def create_goods_search_data(**params):
    defaults = {
        "cateCd": "003024011001",
        "delFl": "n",
        "goodsIconCd": None,
        "goodsIconList": [],
        "goodsNm": "\uac24\ub7ed\uc2dc\uc640\uc774\ub4dc3 \uc561\uc815\ubcf4\ud638\ud544\ub984 2\ub9e41\uc138\ud2b8 SUB \uc9c0\ubb38\ubc29\uc9c0 (SM-J737)",
        "goodsNo": 1007033618,
        "goodsPrice": 3900,
        "goodsSellFl": "y",
        "goodsSellMobileFl": "y",
        "goodsUnitPrice1": 3900.0,
        "goodsUnitPrice10": 3900.0,
        "hitCnt": 22,
        "imageSrc": "https://shop-phinf.pstatic.net/20161027_215/js522b_1477543983102vqxnl_JPEG/1886958591223953_1127973607.jpg?type=m510",
        "orderCnt": 4,
        "orderGoodsCnt": 4,
        "reviewCnt": 0,
        "scmNo": 1297,
        "soldOutFl": "n"
    }
    defaults.update(params)
    return defaults 


add_user_data_url = reverse('crawlapp:add_recommendation_data')

@tag('recommend')
class RecommendationTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.mongo_uri = os.environ.get("MONGO_URI")
        self.mongo_client = MongoClient(self.mongo_uri)
        self.client = APIClient()
        self.db = self.mongo_client.testdb
        self.col = self.db.personalize_table


    
    def test_add_user_data(self):
        user_data = create_user_data()
        response = self.client.post(add_user_data_url,user_data)
        data_list = list(self.col.find({}))
        self.assertEqual(len(data_list),1)
        data = data_list[0]
        for key in user_data.keys():
            self.assertEqual(data[key],user_data[key])



        

    def test_add_user_data_with_original_id(self):
        user_data = create_user_data()
        self.col.insert_one(user_data)
        new_user_data = create_user_data(ORIGINAL_USER_ID='1',USER_ID='2',TIMESTAMP=11113)
        response = self.client.post(add_user_data_url,new_user_data)
        data_list = list(self.col.find({'USER_ID':new_user_data.get("USER_ID")}))
        self.assertEqual(len(data_list),2)
        

            
    def test_aws_utils(self):
        client = boto3.client('personalize-events',region_name='us-east-1')
        stubber = Stubber(client)
        user_data = create_user_data()
        with stubber:
            stubber.add_response('put_events', {})
            add_recommendation_data(client,user_data,'aaaa')


    def test_aws_recommendation_get(self):
        client = boto3.client('personalize-runtime',region_name='us-east-1')
        stubber = Stubber(client)
        user_data = create_user_data()
        aws_return_data = [ {'itemId':str(i+1)} for  i in range(3)]
        with stubber:
            stubber.add_response('get_recommendations',{'itemList':aws_return_data}, {'campaignArn': 'aaaa', 'numResults': 25, 'userId': '1'})
            results = get_recommendation_goods(client,user_data.get("USER_ID"),'aaaa')
            for idx in range(len(results)):
                self.assertEqual(results[idx],int(aws_return_data[idx]['itemId']))



    def test_get_recommended_goods(self):
        data_length = 5
        for i in range(data_length):
            search_data = create_goods_search_data(goodsNo=i+1)
            self.db.goods_search_table.insert_one(search_data)
        query_data={'user_id':'123'}
        get_recommendation_data = reverse('crawlapp:get_recommendation_data',kwargs=query_data)
        query_keys = ['goodsNo','goodsNm','minPrice','maxPrice','imageSrc']
        results = self.client.get(get_recommendation_data)
        data_list = results.data
        self.assertEqual(len(data_list),data_length)
        for key in query_keys:
            for data in data_list:
                self.assertTrue(key in data)
        
        

       



    def tearDown(self):
        super().tearDown()
        self.mongo_client.drop_database('testdb')

        