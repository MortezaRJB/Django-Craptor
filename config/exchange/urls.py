from django.urls import path
from . import views


urlpatterns = [
  path('create-order/', views.OrderCreateAndPlaceApiView.as_view(), name='create-order'),
  path('cancel-order/<str:pk>', views.OrderCancelApiView.as_view(), name='cancel-order'),
  path('orderbooks/', views.OrderBookListApiView.as_view(), name='orderbooks-list'),
  path('orderbooks/<str:pk>', views.OrderBookDetailView.as_view(), name='orderbook-detail'),
]
