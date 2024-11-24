from django import forms
from .models import Invoice, InvoiceItem, Supply
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ['name', 'price', 'quantity']

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item_name', 'base_price']  # Include base_price

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client_name', 'client_email']


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=False, help_text='Optional. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

