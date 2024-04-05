from .models import *
from django.http import HttpResponse
from rest_framework import status
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404
import uuid
from . import utils


def user_balance(user, currency):
  print(type(currency))
  if type(currency) == str:
    # Calculate balance of external transactions
    deposits = UserExternalTransaction.objects.filter(user=user, currency__name__iexact=currency, is_deposit=True).aggregate(Sum('amount'))
    if deposits.get('amount__sum') == None: deposits['amount__sum'] = Decimal('0')
    withdraws = UserExternalTransaction.objects.filter(user=user, currency__name__iexact=currency, is_deposit=False).aggregate(Sum('amount'))
    if withdraws.get('amount__sum') == None: withdraws['amount__sum'] = Decimal('0')
    external_transactions = (deposits.get('amount__sum'))-(withdraws.get('amount__sum'))
    # Calculate balance of internal transactions
    incomings = InternalTransaction.objects.filter(to_user=user, currency__name__iexact=currency).exclude(from_user=F('to_user')).aggregate(Sum('amount'))
    if incomings.get('amount__sum') == None: incomings['amount__sum'] = Decimal('0')
    outgoings = InternalTransaction.objects.filter(from_user=user, currency__name__iexact=currency).exclude(from_user=F('to_user')).aggregate(Sum('amount'))
    if outgoings.get('amount__sum') == None: outgoings['amount__sum'] = Decimal('0')
    internal_transactions = (incomings.get('amount__sum'))-(outgoings.get('amount__sum'))
    # Caluculate the amount of balance which blocked by user orders
    order_blocked_balance = Decimal('0')
    active_order_types = (Order.OrderStatusChoices.PROCESSING, Order.OrderStatusChoices.ACTIVE_NOT_FILLED, Order.OrderStatusChoices.ACTIVE_PARTIALLY_FILLED)
    bid_orders = Order.objects.filter(user=user, is_Bid=True, status__in=active_order_types, orderbook__currency_2=currency.name)
    for order in bid_orders:
      order_blocked_balance += order.size_remained*order.price
    ask_orders = Order.objects.filter(user=user, is_Bid=False, status__in=active_order_types, orderbook__currency_1=currency.name)
    for order in ask_orders:
      order_blocked_balance += order.size_remained
    return (external_transactions)+(internal_transactions)-(order_blocked_balance)
  else:
    # Calculate balance of external transactions
    deposits = UserExternalTransaction.objects.filter(user=user, currency=currency, is_deposit=True).aggregate(Sum('amount'))
    if deposits.get('amount__sum') == None: deposits['amount__sum'] = Decimal('0')
    withdraws = UserExternalTransaction.objects.filter(user=user, currency=currency, is_deposit=False).aggregate(Sum('amount'))
    if withdraws.get('amount__sum') == None: withdraws['amount__sum'] = Decimal('0')
    external_transactions = (deposits.get('amount__sum'))-(withdraws.get('amount__sum'))
    # Calculate balance of internal transactions
    incomings = InternalTransaction.objects.filter(to_user=user, currency=currency).exclude(from_user=F('to_user')).aggregate(Sum('amount'))
    if incomings.get('amount__sum') == None: incomings['amount__sum'] = Decimal('0')
    outgoings = InternalTransaction.objects.filter(from_user=user, currency=currency).exclude(from_user=F('to_user')).aggregate(Sum('amount'))
    if outgoings.get('amount__sum') == None: outgoings['amount__sum'] = Decimal('0')
    internal_transactions = (incomings.get('amount__sum'))-(outgoings.get('amount__sum'))
    # Caluculate the amount of balance which blocked by user orders
    order_blocked_balance = Decimal('0')
    active_order_types = (Order.OrderStatusChoices.PROCESSING, Order.OrderStatusChoices.ACTIVE_NOT_FILLED, Order.OrderStatusChoices.ACTIVE_PARTIALLY_FILLED)
    bid_orders = Order.objects.filter(user=user, is_Bid=True, status__in=active_order_types, orderbook__currency_2=currency)
    for order in bid_orders:
      order_blocked_balance += order.size_remained*order.price
    ask_orders = Order.objects.filter(user=user, is_Bid=False, status__in=active_order_types, orderbook__currency_1=currency)
    for order in ask_orders:
      order_blocked_balance += order.size_remained
    return (external_transactions)+(internal_transactions)-(order_blocked_balance)

def user_requests_crypto_fund(user):
  account = ETHAccounts.objects.select_for_update(skip_locked=True).filter(user=None).first()
  if account:
    account.user = user
    # account.save()
    balance = utils.get_eth_balance(account.public_key)
    currency = get_object_or_404(CryptoCurrencyType, name__iexact='Etherium')
    UserExternalTransaction.objects.create(
      user=user,
      currency=currency,
      is_deposit=True,
      amount=balance,
      from_address=None,
      to_address=account,
    )
    account.save()
  return account

def user_deposits_fiat(user, amount):
  currency = get_object_or_404(CryptoCurrencyType, name__iexact='USD')
  UserExternalTransaction.objects.create(
    user=user,
    currency=currency,
    is_deposit=True,
    amount=amount,
    from_address=None,
    to_address=None,
  )
  return True

def fill_order(existing_order: Order, new_order: Order):
  size_filled = Decimal('0')
  if existing_order.is_Bid:
    bid = existing_order
    ask = new_order
  else:
    bid = new_order
    ask = existing_order

  if existing_order.size_remained >= new_order.size_remained:
      existing_order.size_remained -= new_order.size_remained
      size_filled = new_order.size_remained
      new_order.size_remained = Decimal('0')
  else:
    new_order.size_remained -= existing_order.size_remained
    size_filled = existing_order.size_remained
    existing_order.size_remained = Decimal('0')

  mach = Match()
  mach.bid, mach.ask, mach.size_filled, mach.price = bid, ask, size_filled, existing_order.price
  return mach


def fill(limit: Limit, order: Order):
  matches = []
  listof_orders_to_delete = []
  limit_orders = list(Order.objects.filter(is_limit=True, limit=limit, status__in=[Order.OrderStatusChoices.ACTIVE_NOT_FILLED, Order.OrderStatusChoices.ACTIVE_PARTIALLY_FILLED]))
  for i in range(len(limit_orders)):
    o = limit_orders[i]
    matched = fill_order(o, order)
    limit_orders[i] = o
    # postpone order.save()
    matches.append(matched)
    limit.total_volume -= matched.size_filled
    if limit_orders[i].is_filled:
      limit_orders[i].status = Order.OrderStatusChoices.FILLED
      o.save()
    elif limit_orders[i].size_remained != limit_orders[i].size:
      limit_orders[i].status = Order.OrderStatusChoices.ACTIVE_PARTIALLY_FILLED
      o.save()
    else:
      o.save()
    if order.is_filled:
      order.status = Order.OrderStatusChoices.FILLED
      order.save()
      break
    else: 
      order.save()
  
  return matches

def handle_matches_transaction(orderbook, order, matches):
  if order.is_Bid:
    for mach in matches:
      # TODO: atomic transaction
      InternalTransaction.objects.create(from_user=order.user, to_user=mach.ask.user, currency=orderbook.currency_2, match_transaction=mach, amount=mach.size_filled*mach.price)
      InternalTransaction.objects.create(from_user=mach.ask.user, to_user=order.user, currency=orderbook.currency_1, match_transaction=mach, amount=mach.size_filled)
  else:
    for mach in matches:
      # TODO: atomic transaction
      InternalTransaction.objects.create(from_user=order.user, to_user=mach.bid.user, currency=orderbook.currency_1, match_transaction=mach, amount=mach.size_filled)
      InternalTransaction.objects.create(from_user=mach.bid.user, to_user=order.user, currency=orderbook.currency_2, match_transaction=mach, amount=mach.size_filled*mach.price)

def place_order(order: Order, orderbook: OrderBook):
  # TODO: fix mutex
  if order.is_limit:
    limit, created = Limit.objects.get_or_create(orderbook=orderbook, price=order.price, is_bid=order.is_Bid)
    try:
      order.limit = limit
      order.status = Order.OrderStatusChoices.ACTIVE_NOT_FILLED
      limit.total_volume += order.size
      limit.save()
      order.save()
    except InvalidOperation:
      order.status = Order.OrderStatusChoices.REJECTED
      order.save()
      return HttpResponse(status.HTTP_422_UNPROCESSABLE_ENTITY, 'The Order Size Exceeds The Limit!')
    return HttpResponse(status.HTTP_200_OK, 'The Limit Order Was Placed Successfully.')
  else:
    matches = []
    limits_to_delete = []
    total_vol = Decimal('0')
    limits = list(Limit.objects.filter(orderbook=orderbook, is_bid= not order.is_Bid))
    # Reverse list if order.is_Ask
    if order.is_Bid == False: limits.reverse()
    for l in limits: total_vol += l.total_volume
    if order.size > total_vol:
      order.status = Order.OrderStatusChoices.REJECTED
      order.save()
      return HttpResponse(status.HTTP_422_UNPROCESSABLE_ENTITY, 'The Order Size Exceeds The Limit!')
    else:
      for i in range(len(limits)):
        lim = limits[i]
        there_were_matches = fill(lim, order)
        lim.save()
        limits[i] = lim
        matches.extend(there_were_matches)
        if limits[i].total_volume == Decimal('0'): limits_to_delete.append(limits[i])
      # TODO: fix bulk create for matches
      for m in matches:
        m.save()
      handle_matches_transaction(orderbook, order, matches)
      # TODO: fix bulk delete
      for l in limits_to_delete:
        l.delete()
      return HttpResponse(status.HTTP_200_OK, 'The Market Order Was Placed Successfully.')


