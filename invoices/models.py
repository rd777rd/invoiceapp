from django.db import models

class Supply(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return self.name

class InvoiceItem(models.Model):
    item_name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Add base_price field
    supplies = models.ManyToManyField(Supply)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.00)

    def calculate_total(self):
        self.total = self.base_price + sum(supply.total_price() for supply in self.supplies.all())
        self.save()

    def __str__(self):
        return self.item_name

class Invoice(models.Model):
    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()
    date = models.DateField(auto_now_add=True)
    items = models.ManyToManyField(InvoiceItem)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=True, default=0.00)

    def calculate_total(self):
        self.total = sum(item.total for item in self.items.all())
        self.save()

    def __str__(self):
        return f"Invoice {self.id} - {self.client_name}"
