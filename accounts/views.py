from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from .forms import UserRegistrationForm
from .models import Client, Category, Service, Request as ServiceRequest, TimeTransaction, Report, Review
from django.db.models import Q, Avg
from django.db import transaction
from django.utils import timezone
import json

class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.role or request.user.role.role_name != 'administrador':
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class HomeView(TemplateView):
    template_name = 'home.html'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    login_url = '/login/'

class RegisterView(CreateView):
    template_name = 'register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        from django.contrib.auth import login
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

def validar_username(request):
    username = request.POST.get('username', '')
    if Client.objects.filter(username=username).exists():
        return HttpResponse('<div class="text-red-500 text-sm mt-1">Este nombre de usuario ya está en uso.</div>')
    elif len(username) > 0:
        return HttpResponse('<div class="text-green-500 text-sm mt-1">Nombre de usuario disponible.</div>')
    return HttpResponse('')

def servicios_recientes(request):
    # Placeholders for now
    html = '''
    <div class="bg-gray-50 p-6 rounded-lg text-center text-gray-500">
        Aún no hay servicios recientes.
    </div>
    '''
    return HttpResponse(html)

# --- Admin Panel Views ---
class AdminPanelView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = Client.objects.count()
        context['total_services'] = Service.objects.filter(status='active').count()
        context['categories'] = Category.objects.all().order_by('-created_at')
        context['open_reports'] = Report.objects.filter(report_status__in=['open', 'under_review']).order_by('-created_at')
        return context

def admin_change_report_status(request, pk, status):
    if not request.user.is_authenticated or not request.user.role or request.user.role.role_name != 'administrador':
        return HttpResponse("Unauthorized", status=401)
    
    if request.method == "POST" and status in ['under_review', 'resolved', 'dismissed']:
        report = get_object_or_404(Report, pk=pk)
        report.report_status = status
        
        if status in ['resolved', 'dismissed']:
            report.resolved_at = timezone.now()
        
        # Si se resuelve, suspender al usuario reportado
        if status == 'resolved':
            reported_user = report.reported_client
            reported_user.is_active = False
            reported_user.save()
            
        report.save()
        
        response = HttpResponse("")
        response['HX-Trigger'] = json.dumps({"show-toast": {"message": f"Reporte actualizado a {status}", "type": "success"}})
        return response
    return HttpResponse("Method not allowed", status=405)

def admin_category_list(request):
    if not request.user.is_authenticated or not request.user.role or request.user.role.role_name != 'administrador':
        return HttpResponse("Unauthorized", status=401)
    categories = Category.objects.all().order_by('-created_at')
    return render(request, 'partials/category_table.html', {'categories': categories})

def admin_create_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        desc = request.POST.get('category_description')
        if name:
            Category.objects.create(category_name=name, category_description=desc)
        categories = Category.objects.all().order_by('-created_at')
        return render(request, 'partials/category_table.html', {'categories': categories})
    return HttpResponse("Metodo no permitido", status=405)

def admin_delete_category(request, pk):
    if request.method == "DELETE":
        category = get_object_or_404(Category, pk=pk)
        try:
            category.delete()
            return HttpResponse("")
        except Exception:
            return HttpResponse("<tr><td colspan='4' class='text-red-500 px-6 py-4'>Error: Categoría en uso.</td></tr>")
    return HttpResponse("Metodo no permitido", status=405)

# --- Service Views ---
class ServiceCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'service_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        estimated_time = request.POST.get('estimated_time')
        status = request.POST.get('status', 'active')
        
        category = get_object_or_404(Category, pk=category_id)
        
        Service.objects.create(
            client=request.user,
            category=category,
            title=title,
            description=description,
            estimated_time=estimated_time,
            status=status
        )
        return redirect('service_list')

class ServiceListView(LoginRequiredMixin, TemplateView):
    template_name = 'service_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = Service.objects.filter(status='active').order_by('-created_at')
        context['categories'] = Category.objects.all()
        return context

def search_services(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('categoria', '')
    
    services = Service.objects.filter(status='active')
    
    if query:
        services = services.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category_id:
        services = services.filter(category_id=category_id)
        
    services = services.order_by('-created_at')
    return render(request, 'partials/service_grid.html', {'services': services})

def request_service(request, pk):
    if request.method == "POST":
        service = get_object_or_404(Service, pk=pk)
        horas_solicitadas = float(request.POST.get('requested_hours', service.estimated_time))
        mensaje = request.POST.get('request_message', '')
        
        if float(request.user.time_account.balance_hours) < horas_solicitadas:
            return HttpResponse("Saldo insuficiente", status=400)
            
        request_obj = ServiceRequest.objects.create(
            service=service,
            requester_client=request.user,
            provider_client=service.client,
            request_message=mensaje,
            requested_hours=horas_solicitadas,
            request_status='pending'
        )
        
        # Descontar horas del balance
        request.user.time_account.balance_hours = float(request.user.time_account.balance_hours) - horas_solicitadas
        request.user.time_account.save()
        
        response = HttpResponse("")
        response['HX-Trigger'] = json.dumps({"show-toast": {"message": "¡Solicitud enviada correctamente!", "type": "success"}})
        return response
    return HttpResponse("Method not allowed", status=405)

# --- Requests Inbox Views ---
class RequestsInboxView(LoginRequiredMixin, TemplateView):
    template_name = 'requests_inbox.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['received_requests'] = ServiceRequest.objects.filter(
            provider_client=self.request.user, 
            request_status='pending'
        ).order_by('-requested_at')
        
        context['sent_requests'] = ServiceRequest.objects.filter(
            requester_client=self.request.user
        ).order_by('-requested_at')
        return context

class PendingCountView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        count = ServiceRequest.objects.filter(provider_client=request.user, request_status='pending').count()
        if count > 0:
            return HttpResponse(f'<span class="absolute top-1 right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">{count}</span>')
        return HttpResponse('')

class AcceptRequestView(LoginRequiredMixin, TemplateView):
    def post(self, request, request_id):
        service_req = get_object_or_404(ServiceRequest, pk=request_id, provider_client=request.user, request_status='pending')
        requester = service_req.requester_client
        provider = request.user
        horas = float(service_req.requested_hours)

        try:
            with transaction.atomic():
                # Re-validar saldo del solicitante
                if float(requester.time_account.balance_hours) < horas:
                    # En teoría las horas ya se descontaron, pero si por alguna razón el modelo es distinto:
                    # NOTA: En la lógica de solicitud ya habíamos descontado las horas del balance, así que el requester YA pagó.
                    pass # Asumimos que las horas ya están "retenidas" o ya descontadas de su balance.
                
                # Sin embargo, en el diseño actual las horas se restaron al momento de solicitar.
                # Entonces aquí solo se las sumamos al proveedor.
                provider.time_account.balance_hours = float(provider.time_account.balance_hours) + horas
                provider.time_account.total_hours_earned = float(provider.time_account.total_hours_earned) + horas
                provider.time_account.save()
                
                requester.time_account.total_hours_spent = float(requester.time_account.total_hours_spent) + horas
                requester.time_account.save()
                
                service_req.request_status = 'accepted'
                service_req.responded_at = timezone.now()
                service_req.save()
                
                service_req.service.status = 'completed'
                service_req.service.save()
                
                TimeTransaction.objects.create(
                    request=service_req,
                    sender_client=requester,
                    receiver_client=provider,
                    hours_amount=horas,
                    transaction_type='transfer',
                    transaction_description=f"Pago por servicio: {service_req.service.title}"
                )
                
            response = HttpResponse("")
            response['HX-Trigger'] = json.dumps({"show-toast": {"message": "¡Solicitud aceptada! Horas transferidas.", "type": "success"}})
            return response
        except Exception as e:
            response = HttpResponse("")
            response['HX-Trigger'] = json.dumps({"show-toast": {"message": "Error al aceptar solicitud.", "type": "error"}})
            return response

class RejectRequestView(LoginRequiredMixin, TemplateView):
    def post(self, request, request_id):
        service_req = get_object_or_404(ServiceRequest, pk=request_id, provider_client=request.user, request_status='pending')
        requester = service_req.requester_client
        horas = float(service_req.requested_hours)

        try:
            with transaction.atomic():
                # Devolver horas
                requester.time_account.balance_hours = float(requester.time_account.balance_hours) + horas
                requester.time_account.save()
                
                service_req.request_status = 'rejected'
                service_req.responded_at = timezone.now()
                service_req.save()
                
            response = HttpResponse("")
            response['HX-Trigger'] = json.dumps({"show-toast": {"message": "Solicitud rechazada. Horas devueltas.", "type": "success"}})
            return response
        except Exception as e:
            response = HttpResponse("")
            response['HX-Trigger'] = json.dumps({"show-toast": {"message": "Error al rechazar solicitud.", "type": "error"}})
            return response

# --- Reports ---
class ReportCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'report_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reported_client = get_object_or_404(Client, pk=self.kwargs['client_id'])
        context['reported_client'] = reported_client
        # Solicitudes relacionadas entre los dos
        context['related_requests'] = ServiceRequest.objects.filter(
            Q(requester_client=self.request.user, provider_client=reported_client) |
            Q(requester_client=reported_client, provider_client=self.request.user)
        ).filter(request_status__in=['accepted', 'completed'])
        return context

    def post(self, request, client_id):
        if request.user.pk == client_id:
            return redirect('service_list')
            
        reported_client = get_object_or_404(Client, pk=client_id)
        
        # Verificar si ya existe un reporte abierto
        if Report.objects.filter(reporter_client=request.user, reported_client=reported_client, report_status__in=['open', 'under_review']).exists():
            return redirect('service_list')

        report_reason = request.POST.get('report_reason')
        report_description = request.POST.get('report_description')
        request_id = request.POST.get('request_id')
        
        req_obj = None
        if request_id:
            req_obj = ServiceRequest.objects.filter(pk=request_id).first()

        Report.objects.create(
            reporter_client=request.user,
            reported_client=reported_client,
            request=req_obj,
            report_reason=report_reason,
            report_description=report_description,
            report_status='open'
        )
        # Redirigir al dashboard con un mensaje manual (como no hay django messages, simularemos redirección limpia)
        # En una app real usaríamos messages framework.
        return redirect('dashboard')

# --- Reviews ---
class ReviewCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'review_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        req = get_object_or_404(ServiceRequest, pk=self.kwargs['request_id'], requester_client=self.request.user, request_status='accepted')
        context['service_request'] = req
        
        if Review.objects.filter(request=req).exists():
            context['already_reviewed'] = True
            
        return context

    def post(self, request, request_id):
        req = get_object_or_404(ServiceRequest, pk=request_id, requester_client=request.user, request_status='accepted')
        if Review.objects.filter(request=req).exists():
            return redirect('requests_inbox')
            
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
        
        if rating >= 1 and rating <= 5:
            Review.objects.create(
                request=req,
                reviewer_client=request.user,
                reviewed_client=req.provider_client,
                rating=rating,
                comment=comment
            )
            req.request_status = 'completed'
            req.completed_at = timezone.now()
            req.save()
            
        return redirect('requests_inbox')

class UserReviewsPartialView(TemplateView):
    template_name = 'partials/user_reviews.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = get_object_or_404(Client, pk=self.kwargs['client_id'])
        reviews = Review.objects.filter(reviewed_client=client).order_by('-created_at')
        context['reviews'] = reviews
        context['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg']
        return context
