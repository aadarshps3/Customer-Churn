from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Customer
import pandas as pd
from sklearn.linear_model import LogisticRegression
import numpy as np


def index(request):
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Create a default customer profile
            Customer.objects.create(
                user=user,
                tenure=0,
                monthly_charges=0.0,
                total_charges=0.0,
                contract_type='Month-to-month'
            )
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


def predict_churn(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        customer = Customer.objects.get(user=request.user)
        customer.tenure = int(request.POST['tenure'])
        customer.monthly_charges = float(request.POST['monthly_charges'])
        customer.total_charges = float(request.POST['total_charges'])
        customer.contract_type = request.POST['contract_type']
        customer.save()

        # Mock prediction (simplified Logistic Regression)
        data = pd.DataFrame({
            'tenure': [customer.tenure],
            'monthly_charges': [customer.monthly_charges],
            'total_charges': [customer.total_charges],
            'contract_type': [1 if customer.contract_type == 'One year' else 0]
        })
        model = LogisticRegression()
        # Dummy training data (in real case, you'd train on actual data)
        X_train = pd.DataFrame([[12, 50, 600, 1], [2, 100, 200, 0]],
                               columns=['tenure', 'monthly_charges', 'total_charges', 'contract_type'])
        y_train = [0, 1]  # 0 = no churn, 1 = churn
        model.fit(X_train, y_train)
        prediction = model.predict(data)[0]
        customer.churn_prediction = bool(prediction)
        customer.save()

        return render(request, 'prediction.html', {'prediction': customer.churn_prediction})

    customer = Customer.objects.get(user=request.user)
    return render(request, 'predict.html', {'customer': customer})