from django.db import models
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db.models import QuerySet


class SoftDeletionQuerySet(QuerySet):
  def delete(self):
    return super(SoftDeletionQuerySet, self).update(deleted_at=timezone.now())

  def hard_delete(self):
    return super(SoftDeletionQuerySet, self).delete()

  def alive(self):
    return self.filter(deleted_at=None)

  def dead(self):
    return self.exclude(deleted_at=None)


class SoftDeletionManager(models.Manager):
  def __init__(self, *args, **kwargs) -> None:
    self.alive_only = kwargs.pop('alive_only', True)
    super(SoftDeletionManager, self).__init__(*args, **kwargs)
  
  def get_queryset(self) -> models.QuerySet:
    return super().get_queryset()



class SoftDeletionModel(models.Model):
  deleted_at = models.DateTimeField(null=True, blank=True)

  objects = SoftDeletionManager()
  all_objects = SoftDeletionManager(alive_only=False)

  class Meta:
    abstract = True
  
  def delete(self):
    self.deleted_at = timezone.now()
    self.save()
  
  def hard_delete(self):
    super(SoftDeletionModel, self).delete()


class OrderBook(SoftDeletionModel):
  id  = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False, verbose_name='ID')


class Limit(SoftDeletionModel):
  id              = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False, verbose_name='ID')
  orderbook       = models.ForeignKey(OrderBook, related_name='limits', on_delete=models.CASCADE)
  is_bid          = models.BooleanField()
  price           = models.DecimalField(max_digits=settings.DECIMAL_FIELDS_ATTRIBUTES['limit_price']['max_digits'], decimal_places=settings.DECIMAL_FIELDS_ATTRIBUTES['limit_price']['decimal_places'])
  total_volume    = models.DecimalField(default=Decimal('0'), max_digits=settings.DECIMAL_FIELDS_ATTRIBUTES['limit_total_volume']['max_digits'], decimal_places=settings.DECIMAL_FIELDS_ATTRIBUTES['limit_total_volume']['decimal_places'])

  class Meta:
    ordering = ['price']
    models.UniqueConstraint(fields=['orderbook', 'price'], name='unique_limit_at_any_price')


class Order(SoftDeletionModel):

  class OrderStatusChoices(models.TextChoices):
    FILLED                      = 'Filled'
    PROCESSING                  = 'Processing'
    ACTIVE_NOT_FILLED           = 'Active_Not_Filled'
    ACTIVE_PARTIALLY_FILLED     = 'Active_Partially_Filled'
    REJECTED                    = 'Rejected'
    CANCELLED_NOT_FILLED        = 'Cancelled_Not_Filled'
    CANCELLED_PARTIALLY_FILLED  = 'Cancelled_Partially_Filled'

  id            = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False, verbose_name='ID')
  size          = models.DecimalField(max_digits=settings.DECIMAL_FIELDS_ATTRIBUTES['order_size']['max_digits'], decimal_places=settings.DECIMAL_FIELDS_ATTRIBUTES['order_size']['decimal_places'])
  size_remained = models.DecimalField(max_digits=settings.DECIMAL_FIELDS_ATTRIBUTES['order_size']['max_digits'], decimal_places=settings.DECIMAL_FIELDS_ATTRIBUTES['order_size']['decimal_places'])
  is_Bid        = models.BooleanField()
  price         = models.DecimalField(null=True, blank=True, max_digits=settings.DECIMAL_FIELDS_ATTRIBUTES['order_price']['max_digits'], decimal_places=settings.DECIMAL_FIELDS_ATTRIBUTES['order_price']['decimal_places'])
  is_limit      = models.BooleanField()
  limit         = models.ForeignKey(Limit, default=None, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
  status        = models.CharField(max_length=50, choices=OrderStatusChoices.choices)
  timestamp     = models.DateTimeField(auto_now_add=True)

  @property
  def is_filled(self):
    return self.size_remained == 0


class Match(SoftDeletionModel):
  id              = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False, verbose_name='ID')
  bid             = models.ForeignKey(Order, related_name='bid_matches', on_delete=models.CASCADE)
  ask             = models.ForeignKey(Order, related_name='ask_matches', on_delete=models.CASCADE)
  size_filled     = models.DecimalField(max_digits=settings.DECIMAL_FIELDS_ATTRIBUTES['match_size_filled']['max_digits'], decimal_places=settings.DECIMAL_FIELDS_ATTRIBUTES['match_size_filled']['decimal_places'])
  price           = models.DecimalField(max_digits=settings.DECIMAL_FIELDS_ATTRIBUTES['match_price']['max_digits'], decimal_places=settings.DECIMAL_FIELDS_ATTRIBUTES['match_price']['decimal_places'])

