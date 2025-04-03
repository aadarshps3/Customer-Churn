# detector/admin.py
from django.contrib import admin
from .models import Customer, ChurnPredictionHistory, Product, PurchaseHistory, Interaction

admin.site.register(Customer)
admin.site.register(ChurnPredictionHistory)
admin.site.register(Product)
admin.site.register(PurchaseHistory)
admin.site.register(Interaction)