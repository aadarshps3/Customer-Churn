from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenure = models.IntegerField()  # Months with company
    monthly_charges = models.FloatField()
    total_charges = models.FloatField()
    contract_type = models.CharField(max_length=20)  # e.g., 'Month-to-month', 'One year'
    churn_prediction = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Customer Data"