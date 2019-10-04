from django.urls import path, include, re_path
from . import views
from rest_framework import routers

app_name = 'crawlapp'

router = routers.DefaultRouter()
# router.register('products', views.GetAllProductsView)

urlpatterns = [
    # path('', include(router.urls)),
    path('', views.TestView.as_view(), name='hellowrold'),
    path('product/<int:goodsNo>/', views.ProductView.as_view(), name='products'),
    path('category/<str:cateCd>/', views.CategoryView.as_view(), name='category'),
    path('personalize/', views.PersonalizeView.as_view(), name='personalize'),
    path('add_recommendation_data/', views.AddUserView.as_view(), name='add_recommendation_data'),
    path('get_recommendation_data/<slug:user_id>/', views.GetRecommendGoodsView.as_view(),name='get_recommendation_data' ),
    
]


# GET: /api/ 전체상품 불러오기
# GET: /api/$goodsNo 해당 상품 불러오기
# POST: /api/ 상품 추가하기
# GET: /api/$cat 관련상품 불러오기
