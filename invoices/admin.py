from django.contrib import admin
from .models import Invoice, InvoiceItem,Supply

# Register your models here.
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Supply)