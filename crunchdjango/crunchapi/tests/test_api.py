from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from pymongo import MongoClient
import os
from rest_framework import status

test_get_url = reverse('crawlapp:hellowrold')
# test_get_category = '/api/category/'



class StockTest(SimpleTestCase):
    allow_database_queries = True

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.mongo_client = MongoClient(os.environ.get('MONGO_URI'))
        self.db = self.mongo_client.test_db
        self.goods_search_table = self.db.goods_search_table

        print('self $@$!@#$!#$%#@%', self)
        # test_get_category = reverse("crawlapp:category", kwargs={
        #         "cateCd": self.company.pk})

    # post 1 data

    def test_check_data(self):
        data = {
            "cateCd": "009006018",
            "goodsNm": "\ub098\uc774\ud0a4 \ub0a8\uc131 \ud074\ub7fd \ud0f1\ud06c \ub098\uc2dc\ud2f0 BQ1260-010",
        }
        response = self.client.post(test_get_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(test_get_url)
        self.assertEqual(response.data[0], data)

        print(test_get_url, test_get_category + '009005001')

    # post 5 datas

    def test_check_data_5(self):
        data = [{
            "cateCd": "009006018",
            "goodsNm": "\ub098\uc774\ud0a4 \ub0a8\uc131 \ud074\ub7fd \ud0f1\ud06c \ub098\uc2dc\ud2f0 BQ1260-010",
        }, {
            "cateCd": "010024003",
            "goodsNm": "[\uc544\ub791\ub85c\ub791] \ud504\ub9ac\ud2f0\uc2a4\ud33d\uae00\ub9ac\ubcf8 \uba38\ub9ac\ub760 \ud558\ub4dc\ud615",
        }, {
            "cateCd": "009001004001",
            "goodsNm": "\ub7ed\uc13c\uc2a4 \ub0a8\uc131\ub0b4\uc758 \uc5d0\uc2a4\ubbf8\uc5b4 \uc18c\uc7ac\ub85c \uac00\ubcbc\uc6b4 \uc2dc\uc98c\ub0b4\uc758",
        }, {
            "cateCd": "010024003",
            "goodsNm": "[\uc544\ub791\ub85c\ub791] \ud504\ub9ac\ud2f0\uc2a4\ud33d\uae00\ub9ac\ubcf8 \uc544\uae30\ud5e4\uc5b4\ubc34\ub4dc",
        }, {
            "cateCd": "009005001",
            "goodsNm": "\ub9ac\ubca0\uc559 \ub7f0\ub2dd \ubd80\ub4dc\ub7ec\uc6b4 \uc2ac\ub9bd \uc5ec\uc131 \uce90\ubbf8\uc194 \uc5b8\ub354\uc6e8\uc5b4"
        }]
        response = self.client.post(test_get_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(test_get_url)
        self.assertEqual(len(response.data), len(data))

        for i in range(len(data)):
            self.assertEqual(
                len(response.data[i]['goodsNm']), len(data[i]['goodsNm']))

    def test_check_category(self):
        data = [{
            "cateCd": "009006018",
            "goodsNm": "\ub098\uc774\ud0a4 \ub0a8\uc131 \ud074\ub7fd \ud0f1\ud06c \ub098\uc2dc\ud2f0 BQ1260-010",
        }, {
            "cateCd": "010024003",
            "goodsNm": "[\uc544\ub791\ub85c\ub791] \ud504\ub9ac\ud2f0\uc2a4\ud33d\uae00\ub9ac\ubcf8 \uba38\ub9ac\ub760 \ud558\ub4dc\ud615",
        }, {
            "cateCd": "009001004001",
            "goodsNm": "\ub7ed\uc13c\uc2a4 \ub0a8\uc131\ub0b4\uc758 \uc5d0\uc2a4\ubbf8\uc5b4 \uc18c\uc7ac\ub85c \uac00\ubcbc\uc6b4 \uc2dc\uc98c\ub0b4\uc758",
        }, {
            "cateCd": "010024003",
            "goodsNm": "[\uc544\ub791\ub85c\ub791] \ud504\ub9ac\ud2f0\uc2a4\ud33d\uae00\ub9ac\ubcf8 \uc544\uae30\ud5e4\uc5b4\ubc34\ub4dc",
        }, {
            "cateCd": "009005001",
            "goodsNm": "\ub9ac\ubca0\uc559 \ub7f0\ub2dd \ubd80\ub4dc\ub7ec\uc6b4 \uc2ac\ub9bd \uc5ec\uc131 \uce90\ubbf8\uc194 \uc5b8\ub354\uc6e8\uc5b4"
        }]

        response = self.client.post(test_get_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get('/api/category/%s/' % '009005001')
        print('$$$@Q#$!#$!#$!#', response.data)
        self.assertEqual(len(response), 3)

    def tearDown(self):
        super().tearDown()
        self.mongo_client.drop_database('test_db')
        self.mongo_client.close()
