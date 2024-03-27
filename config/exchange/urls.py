from django.urls import path
from . import views


urlpatterns = [
  path('create-order/', views.OrderCreateAndPlaceApiView.as_view(), name='create-order'),
  path('cancel-order/<str:pk>', views.OrderCancelApiView.as_view(), name='cancel-order'),
]

