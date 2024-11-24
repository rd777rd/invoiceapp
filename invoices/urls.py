# urls.py
from django.urls import path,include
from django.contrib.auth import views as auth_views
from .views import InvoiceListView, CreateInvoiceView, CreateSupplyView, CreateInvoiceItemView,custom_logout_view, signup,custom_404_view

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('signup/', signup, name='signup'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('create-invoice/', CreateInvoiceView.as_view(), name='create_invoice'),
    path('create-supply/', CreateSupplyView.as_view(), name='create_supply'),
    path('create-invoice-item/', CreateInvoiceItemView.as_view(), name='create_invoice_item'),
]

