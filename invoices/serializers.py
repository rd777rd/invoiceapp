from rest_framework import serializers
from .models import Invoice, InvoiceItem, Supply

class SupplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Supply
        fields = '__all__'

class InvoiceItemSerializer(serializers.ModelSerializer):
    supplies = SupplySerializer(many=True)

    class Meta:
        model = InvoiceItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = '__all__'
