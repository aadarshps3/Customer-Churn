# detector/models.py
from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenure = models.IntegerField(default=0)
    monthly_charges = models.FloatField(default=0.0)
    total_charges = models.FloatField(default=0.0)
    contract_type = models.CharField(max_length=20, default='Month-to-month')
    churn_prediction = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ChurnPredictionHistory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='prediction_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    churn_prediction = models.BooleanField()
    tenure = models.IntegerField()
    monthly_charges = models.FloatField()
    total_charges = models.FloatField()
    contract_type = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.customer.user.username} - {self.timestamp}"


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.FloatField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # Add image field

    def __str__(self):
        return self.name


class PurchaseHistory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='purchase_history')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()

    def __str__(self):
        return f"{self.customer.user.username} - {self.product.name} - {self.purchase_date}"


class Interaction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'Page View'),
        ('click', 'Click'),
        ('recommendation_view', 'Recommendation Viewed'),
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    details = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.interaction_type} - {self.timestamp}"