# detector/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Customer, ChurnPredictionHistory, Product, PurchaseHistory, Interaction
import pandas as pd
from sklearn.linear_model import LogisticRegression
import numpy as np
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO


def index(request):
    if request.user.is_authenticated:
        if request.user.username == 'Admin':
            return redirect('admin_dashboard')
        return redirect('user_dashboard')
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            Customer.objects.create(
                user=user,
                tenure=0,
                monthly_charges=0.0,
                total_charges=0.0,
                contract_type='Month-to-month'
            )
            return redirect('user_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        username = request.POST['username']
        password = request.POST['password']

        if username == 'Admin' and password == '123':
            user = authenticate(request, username=username, password=password)
            if user is None:
                from django.contrib.auth.models import User
                try:
                    user = User.objects.create_user(username='Admin', password='123')
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                except:
                    return render(request, 'login.html', {
                        'form': form,
                        'error': 'Admin user creation failed. Please try again.'
                    })
            login(request, user)
            return redirect('admin_dashboard')

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('user_dashboard')
        else:
            return render(request, 'login.html', {
                'form': form,
                'error': 'Invalid username or password.'
            })
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


def get_product_recommendation(customer):
    recommendations = []
    history = customer.prediction_history.all().order_by('-timestamp')[:5]
    purchases = customer.purchase_history.all().order_by('-purchase_date')[:5]
    interactions = customer.interactions.all().order_by('-timestamp')[:10]

    churn_count = sum(1 for pred in history if pred.churn_prediction)
    churn_rate = churn_count / max(len(history), 1)
    total_spent = sum(purchase.amount for purchase in purchases)
    purchase_frequency = len(purchases)

    current_tenure = customer.tenure
    current_monthly_charges = customer.monthly_charges

    if current_tenure < 6 or current_monthly_charges < 50:
        recommendations.append({
            'name': 'Basic Plan',
            'description': 'Affordable plan for new or low-usage customers ($30/month).',
            'image': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c',
            'delay': 0.1
        })
    if current_tenure > 12 or current_monthly_charges > 80 or total_spent > 500:
        recommendations.append({
            'name': 'Premium Plan',
            'description': 'Enhanced features for loyal customers ($100/month).',
            'image': 'https://images.unsplash.com/photo-1556740738-b6a63e27c4df',
            'delay': 0.2
        })
    if churn_rate > 0.5:
        recommendations.append({
            'name': 'Retention Offer',
            'description': 'Special discount: 20% off your next bill to stay with us!',
            'image': 'https://www.marketing91.com/wp-content/uploads/2020/02/What-is-Retention-Bonus.jpg',
            'delay': 0.3
        })
    elif customer.churn_prediction:
        recommendations.append({
            'name': 'Loyalty Bonus',
            'description': 'Stay with us and get a $10 credit on your next bill.',
            'image': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c',
            'delay': 0.3
        })
    if churn_rate == 0 and len(history) >= 3 and purchase_frequency >= 3:
        recommendations.append({
            'name': 'Upgrade Bundle',
            'description': 'Add premium features for just $15/month more.',
            'image': 'https://images.unsplash.com/photo-1556740738-b6a63e27c4df',
            'delay': 0.4
        })
    if any(interaction.interaction_type == 'view' and 'predict' in interaction.details.lower() for interaction in interactions):
        recommendations.append({
            'name': 'Analytics Add-On',
            'description': 'Get detailed churn analytics for $5/month.',
            'image': 'https://cdn-icons-png.freepik.com/512/7731/7731130.png',
            'delay': 0.5
        })
    if not recommendations:
        recommendations.append({
            'name': 'Standard Plan',
            'description': 'Balanced option for all customers ($60/month).',
            'image': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c',
            'delay': 0.1
        })
    return recommendations


@login_required
def user_dashboard(request):
    if request.user.username == 'Admin':
        return redirect('admin_dashboard')

    customer = Customer.objects.get(user=request.user)
    recommendations = get_product_recommendation(customer)

    # Track interaction
    Interaction.objects.create(
        customer=customer,
        interaction_type='view',
        details='Viewed user dashboard'
    )
    for rec in recommendations:
        Interaction.objects.create(
            customer=customer,
            interaction_type='recommendation_view',
            details=f"Viewed recommendation: {rec['name']}"
        )

    return render(request, 'user_dashboard.html', {
        'customer': customer,
        'recommendations': recommendations,
    })


@login_required
def purchase_product(request):
    if request.user.username == 'Admin':
        return redirect('admin_dashboard')

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        customer = Customer.objects.get(user=request.user)

        # Find the product in the database (if it exists)
        try:
            product = Product.objects.get(name=product_name)
            # Log the purchase
            PurchaseHistory.objects.create(
                customer=customer,
                product=product,
                amount=product.price
            )
        except Product.DoesNotExist:
            # If the product isn't in the database (e.g., Retention Offer, Loyalty Bonus), log a dummy purchase
            try:
                product = Product.objects.get(name=product_name)
            except Product.DoesNotExist:
                # Create a dummy product if it doesn't exist
                price = 0.0
                description = "Special offer"
                if product_name == "Retention Offer":
                    price = 0.0  # Discount, so price is 0
                    description = "Special discount: 20% off your next bill to stay with us!"
                elif product_name == "Loyalty Bonus":
                    price = 0.0  # Credit, so price is 0
                    description = "Stay with us and get a $10 credit on your next bill."
                elif product_name == "Basic Plan":
                    price = 30.0
                    description = "Affordable plan for new or low-usage customers ($30/month)."
                elif product_name == "Premium Plan":
                    price = 100.0
                    description = "Enhanced features for loyal customers ($100/month)."
                elif product_name == "Upgrade Bundle":
                    price = 15.0
                    description = "Add premium features for just $15/month more."
                elif product_name == "Analytics Add-On":
                    price = 5.0
                    description = "Get detailed churn analytics for $5/month."
                elif product_name == "Standard Plan":
                    price = 60.0
                    description = "Balanced option for all customers ($60/month)."
                product = Product.objects.create(
                    name=product_name,
                    description=description,
                    price=price
                )
            PurchaseHistory.objects.create(
                customer=customer,
                product=product,
                amount=product.price
            )

        # Log the interaction
        Interaction.objects.create(
            customer=customer,
            interaction_type='click',
            details=f"Purchased product: {product_name}"
        )

        return redirect('user_dashboard')

    return redirect('user_dashboard')


@login_required
def predict_churn(request):
    if request.user.username == 'Admin':
        return redirect('admin_dashboard')

    customer = Customer.objects.get(user=request.user)
    Interaction.objects.create(
        customer=customer,
        interaction_type='view',
        details='Viewed predict page'
    )

    if request.method == 'POST':
        customer.tenure = int(request.POST['tenure'])
        customer.monthly_charges = float(request.POST['monthly_charges'])
        customer.total_charges = float(request.POST['total_charges'])
        customer.contract_type = request.POST['contract_type']
        customer.save()

        data = pd.DataFrame({
            'tenure': [customer.tenure],
            'monthly_charges': [customer.monthly_charges],
            'total_charges': [customer.total_charges],
            'contract_type': [1 if customer.contract_type == 'One year' else 0]
        })
        model = LogisticRegression()
        X_train = pd.DataFrame([[12, 50, 600, 1], [2, 100, 200, 0]],
                               columns=['tenure', 'monthly_charges', 'total_charges', 'contract_type'])
        y_train = [0, 1]
        model.fit(X_train, y_train)
        prediction = model.predict(data)[0]
        customer.churn_prediction = bool(prediction)
        customer.save()

        ChurnPredictionHistory.objects.create(
            customer=customer,
            churn_prediction=customer.churn_prediction,
            tenure=customer.tenure,
            monthly_charges=customer.monthly_charges,
            total_charges=customer.total_charges,
            contract_type=customer.contract_type
        )

        recommendations = get_product_recommendation(customer)
        for rec in recommendations:
            Interaction.objects.create(
                customer=customer,
                interaction_type='recommendation_view',
                details=f"Viewed recommendation: {rec['name']}"
            )

        return render(request, 'prediction.html', {
            'prediction': customer.churn_prediction,
            'recommendations': recommendations,
            'customer': customer,
        })

    recommendations = get_product_recommendation(customer)
    for rec in recommendations:
        Interaction.objects.create(
            customer=customer,
            interaction_type='recommendation_view',
            details=f"Viewed recommendation: {rec['name']}"
        )

    return render(request, 'predict.html', {
        'customer': customer,
        'recommendations': recommendations
    })


@login_required
def admin_dashboard(request):
    if not request.user.username == 'Admin':
        return redirect('user_dashboard')

    customers = Customer.objects.all()
    predictions = ChurnPredictionHistory.objects.all().order_by('-timestamp')[:50]
    purchases = PurchaseHistory.objects.all().order_by('-purchase_date')[:50]
    interactions = Interaction.objects.all().order_by('-timestamp')[:50]
    products = Product.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_product':
            name = request.POST.get('product_name')
            description = request.POST.get('product_description')
            price = float(request.POST.get('product_price'))
            Product.objects.create(name=name, description=description, price=price)
        elif action == 'delete_customer':
            customer_id = request.POST.get('customer_id')
            Customer.objects.filter(id=customer_id).delete()
        elif action == 'add_purchase':
            customer_id = request.POST.get('customer_id')
            product_id = request.POST.get('product_id')
            customer = Customer.objects.get(id=customer_id)
            product = Product.objects.get(id=product_id)
            PurchaseHistory.objects.create(customer=customer, product=product, amount=product.price)
        return redirect('admin_dashboard')

    return render(request, 'admin_dashboard.html', {
        'customers': customers,
        'predictions': predictions,
        'purchases': purchases,
        'interactions': interactions,
        'products': products,
    })


@login_required
def download_report(request):
    if request.user.username == 'Admin':
        return redirect('admin_dashboard')

    customer = Customer.objects.get(user=request.user)
    recommendations = get_product_recommendation(customer)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Churn Prediction Report")

    p.setFont("Helvetica", 12)
    y = height - 100
    p.drawString(100, y, f"Username: {customer.user.username}")
    y -= 20
    p.drawString(100, y, f"Tenure: {customer.tenure} months")
    y -= 20
    p.drawString(100, y, f"Monthly Charges: ${customer.monthly_charges}")
    y -= 20
    p.drawString(100, y, f"Total Charges: ${customer.total_charges}")
    y -= 20
    p.drawString(100, y, f"Contract Type: {customer.contract_type}")
    y -= 20
    p.drawString(100, y, f"Churn Prediction: {'Yes' if customer.churn_prediction else 'No'}")

    y -= 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, y, "Recommended Products")
    p.setFont("Helvetica", 12)
    y -= 20
    for rec in recommendations:
        p.drawString(100, y, f"- {rec['name']}: {rec['description']}")
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50

    p.setFont("Helvetica", 10)
    p.drawString(100, 30, "Generated on: April 03, 2025")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="churn_report.pdf"'
    return response