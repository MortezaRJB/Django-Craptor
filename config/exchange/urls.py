from django.urls import path
from . import views


urlpatterns = [
  path('user-balance/<str:currency>', views.GetUserBalanceApiView.as_view(), name='user-balance'),
  path('create-order/', views.OrderCreateAndPlaceApiView.as_view(), name='create-order'),
  path('cancel-order/<str:pk>', views.OrderCancelApiView.as_view(), name='cancel-order'),
  path('orderbooks/', views.OrderBookListApiView.as_view(), name='orderbooks-list'),
  path('orderbooks/<str:pk>', views.OrderBookDetailView.as_view(), name='orderbook-detail'),
  path('deposit-fiat/', views.UserDepositsFiatApiView.as_view(), name='deposit-fiat'),
  path('request-crypto-fund/', views.UserRequestsCryptoFundApiView.as_view(), name='request-crypto-fiat'),
  # Admin Only:
  path('gather-eth-accounts/', views.GatherETHAccounts.as_view(), name='gather-eth-accounts'),
]

