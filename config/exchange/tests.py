from django.test import TestCase, Client
from . import models
from decimal import Decimal
from django.urls import reverse
from rest_framework import status


class TestOrderViews(TestCase):
  def setUp(self) -> None:
    self.client = Client()
    self.ob = models.OrderBook.objects.create(currency_1='ETH', currency_2='USD')
  
  def test_limit_order_create_view(self):
    buy_limit_order = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('10'),
      'is_Bid': True,
      'price': Decimal('10000'),
      'is_limit': True,
    })
    sell_limit_order_1 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('5'),
      'is_Bid': False,
      'price': Decimal('8500'),
      'is_limit': True,
    })
    sell_limit_order_2 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('3'),
      'is_Bid': False,
      'price': Decimal('8500'),
      'is_limit': True,
    })
    limits = models.Limit.all_objects.all()

    self.assertEqual(buy_limit_order.status_code, status.HTTP_201_CREATED)
    self.assertEqual(sell_limit_order_1.status_code, status.HTTP_201_CREATED)
    self.assertEqual(sell_limit_order_2.status_code, status.HTTP_201_CREATED)
    self.assertEqual(len(limits), 2)
    self.assertEqual(limits[1].total_volume, Decimal('10'))
    self.assertEqual(limits[1].price, Decimal('10000'))
    self.assertEqual(limits[0].total_volume, Decimal('8'))

  
  def test_singlefill_market_order_create_view(self):
    sell_limit_order = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('10'),
      'is_Bid': False,
      'price': Decimal('10000'),
      'is_limit': True,
    })
    limits = models.Limit.all_objects.all()

    self.assertEqual(sell_limit_order.status_code, status.HTTP_201_CREATED)
    self.assertEqual(len(limits), 1)
    self.assertEqual(limits[0].total_volume, Decimal('10'))

    response = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('7'),
      'is_Bid': True,
      'is_limit': False,
    })
    buy_market_order = models.Order.all_objects.get(is_Bid=True, size=Decimal('7'))
    sell_order = models.Order.all_objects.get(is_Bid=False, size=Decimal('10'))
    limits = limits = models.Limit.all_objects.all()
    matches = models.Match.all_objects.filter(bid=buy_market_order)

    self.assertEqual(len(limits), 1)
    self.assertEqual(len(matches), 1)
    self.assertEqual(matches[0].ask, sell_order)
    self.assertEqual(matches[0].size_filled, Decimal('7'))
    self.assertEqual(matches[0].price, Decimal('10000'))
  
  def test_multifill_market_order_create_view(self):
    buy_limit_order_1 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('4'),
      'is_Bid': True,
      'price': Decimal('9000'),
      'is_limit': True,
    })
    buy_limit_order_2 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('5'),
      'is_Bid': True,
      'price': Decimal('7000'),
      'is_limit': True,
    })
    buy_limit_order_3 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('15'),
      'is_Bid': True,
      'price': Decimal('10000'),
      'is_limit': True,
    })
    limits = models.Limit.all_objects.all()
    limits_total_vol = Decimal('0')
    for limit in limits: limits_total_vol += limit.total_volume

    self.assertEqual(buy_limit_order_1.status_code, status.HTTP_201_CREATED)
    self.assertEqual(buy_limit_order_2.status_code, status.HTTP_201_CREATED)
    self.assertEqual(buy_limit_order_3.status_code, status.HTTP_201_CREATED)
    self.assertEqual(len(limits), 3)
    self.assertEqual(limits_total_vol, Decimal('24'))

    response = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('20.9'),
      'is_Bid': False,
      'is_limit': False,
    })
    limits = models.Limit.all_objects.all()
    alive_limits = limits.filter(deleted_at=None)
    limits_total_vol = Decimal('0')
    for limit in limits: limits_total_vol += limit.total_volume
    matches = models.Match.all_objects.all()

    self.assertEqual(len(limits), 3)
    self.assertEqual(limits_total_vol, Decimal('3.1'))
    self.assertEqual(len(matches), 3)
    # print(f'\n==> Matches: ', [mtch.size_filled for mtch in matches])
    self.assertEqual(len(alive_limits), 1)

  def test_cancel_order(self):
    # NOT FILLED LIMIT CANCEL
    buy_limit_order_1 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('10'),
      'is_Bid': True,
      'price': Decimal('10000'),
      'is_limit': True,
    })

    response_1 = self.client.delete(reverse('cancel-order', kwargs={'pk': buy_limit_order_1.data.get('id')}))
    the_order_1 = models.Order.objects.get(pk=buy_limit_order_1.data.get('id'))

    self.assertEqual(response_1.status_code, status.HTTP_204_NO_CONTENT)
    self.assertEqual(the_order_1.status, models.Order.OrderStatusChoices.CANCELLED_NOT_FILLED)

    # PARTIALLY FILLED LIMIT CANCEL
    sell_limit_order_1 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('10'),
      'is_Bid': False,
      'price': Decimal('10000'),
      'is_limit': True,
    })
    buy_market_order_2 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('7'),
      'is_Bid': True,
      'is_limit': False,
    })

    response_2 = self.client.delete(reverse('cancel-order', kwargs={'pk': sell_limit_order_1.data.get('id')}))
    the_order_2 = models.Order.objects.get(pk=sell_limit_order_1.data.get('id'))

    self.assertEqual(response_2.status_code, status.HTTP_204_NO_CONTENT)
    self.assertEqual(the_order_2.status, models.Order.OrderStatusChoices.CANCELLED_PARTIALLY_FILLED)

    # CAN NOT CANCEL
    sell_limit_order = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('10'),
      'is_Bid': False,
      'price': Decimal('10000'),
      'is_limit': True,
    })
    buy_market_order_3 = self.client.post(reverse('create-order'), {
      'orderbook': self.ob.id,
      'size': Decimal('10'),
      'is_Bid': True,
      'is_limit': False,
    })

    response_3 = self.client.delete(reverse('cancel-order', kwargs={'pk': buy_market_order_2.data.get('id')}))
    the_order_3 = models.Order.objects.get(pk=buy_market_order_2.data.get('id'))

    self.assertEqual(response_3.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertEqual(the_order_3.status, models.Order.OrderStatusChoices.FILLED)




