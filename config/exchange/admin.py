from django.contrib import admin
from . import models


admin.site.register(models.OrderBook)
admin.site.register(models.Limit)
admin.site.register(models.Order)
admin.site.register(models.Match)
admin.site.register(models.ETHAccounts)
admin.site.register(models.CryptoCurrencyType)
admin.site.register(models.UserExternalTransaction)
admin.site.register(models.InternalTransaction)
