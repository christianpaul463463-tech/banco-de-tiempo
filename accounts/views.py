from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from .forms import UserRegistrationForm
from .models import Client, Category, Service, Request as ServiceRequest
from django.db.models import Q
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
        return context

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
        response['HX-Trigger'] = json.dumps({"show-toast": {"message": "¡Solicitud enviada correctamente!"}})
        return response
    return HttpResponse("Method not allowed", status=405)
