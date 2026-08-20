from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from . import email_service
from .models import Invoice, InvoiceItem, Supply
from .forms import InvoiceForm, InvoiceItemForm, SupplyForm, SignUpForm
from django.shortcuts import redirect

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoice_list.html'
    context_object_name = 'invoices'
    login_url = 'login'


class CreateInvoiceView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        invoice_form = InvoiceForm()
        items = InvoiceItem.objects.all()
        return render(request, 'create_invoice.html', {
            'invoice_form': invoice_form,
            'items': items
        })

    def post(self, request, *args, **kwargs):
        invoice_form = InvoiceForm(request.POST)
        selected_items = request.POST.getlist('item')

        if invoice_form.is_valid():
            invoice = invoice_form.save()

            for item_id in selected_items:
                item = InvoiceItem.objects.get(id=item_id)
                invoice.items.add(item)
                item.calculate_total()

            invoice.calculate_total()
            send_invoice_email(invoice)
            return redirect('invoice_list')
        else:
            items = InvoiceItem.objects.all()
            return render(request, 'create_invoice.html', {
                'invoice_form': invoice_form,
                'items': items
            })


class CreateSupplyView(LoginRequiredMixin, CreateView):
    model = Supply
    form_class = SupplyForm
    template_name = 'create_supply.html'
    success_url = reverse_lazy('create_invoice')
    login_url = 'login'


class CreateInvoiceItemView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        invoice_item_form = InvoiceItemForm()
        supplies = Supply.objects.all()
        return render(request, 'create_invoice_item.html', {
            'supplies': supplies,
            'invoice_item_form': invoice_item_form
        })

    def post(self, request, *args, **kwargs):
        invoice_item_form = InvoiceItemForm(request.POST)
        if invoice_item_form.is_valid():
            item = invoice_item_form.save()
            selected_supplies = request.POST.getlist('supplies')
            for supply_id in selected_supplies:
                supply = Supply.objects.get(id=supply_id)
                item.supplies.add(supply)
            item.total = sum(supply.total_price() for supply in item.supplies.all()) 
            item.save()
            return redirect('create_invoice')
        else:
            supplies = Supply.objects.all()
            return render(request, 'create_invoice_item.html', {
                'supplies': supplies,
                'invoice_item_form': invoice_item_form
            })


def generate_invoice_pdf(invoice):
    # No `request` is passed to render() here, so template context
    # processors (including the branding one -- see context_processors.py)
    # never run. company_name has to be supplied explicitly.
    template = get_template('pdf_invoice_template.html')
    html = template.render({'invoice': invoice, 'company_name': settings.COMPANY_NAME})
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result)
    if not pdf.err:
        return result.getvalue()
    return None


def send_invoice_email(invoice):
    """Best-effort: generates the PDF and emails it via Brevo (see
    email_service.py). Never raises -- a failed/unconfigured email send
    must not break invoice creation, which already saved successfully by
    the time this is called. (The previous SMTP version called
    EmailMessage.send() with no error handling at all, so an SMTP failure
    -- guaranteed on Render's free tier, which blocks outbound SMTP --
    could 500 the entire "create invoice" request even though the invoice
    itself had already been saved to the database.)"""
    pdf = generate_invoice_pdf(invoice)
    email_service.send_invoice_email(invoice, pdf)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.email = form.cleaned_data.get('email')
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('invoice_list')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def custom_logout_view(request):
     logout(request) 
     return redirect('login')

def custom_404_view(request, exception):
    return redirect('invoice_list')
