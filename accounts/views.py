from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from .forms import UserRegistrationForm
from .models import User

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
    if User.objects.filter(username=username).exists():
        return HttpResponse('<div class="text-red-500 text-sm mt-1">Este nombre de usuario ya está en uso.</div>')
    elif len(username) > 0:
        return HttpResponse('<div class="text-green-500 text-sm mt-1">Nombre de usuario disponible.</div>')
    return HttpResponse('')

def servicios_recientes(request):
    # This is a placeholder for HTMX to load recent services
    import time
    time.sleep(1)  # Simulate loading
    html = '''
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100">
            <h3 class="text-lg font-bold text-gray-800 mb-2">Clases de Inglés Conversacional</h3>
            <p class="text-gray-600 text-sm mb-4">Ofrecido por: Maria G.</p>
            <div class="flex justify-between items-center">
                <span class="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded">Idiomas</span>
                <span class="text-indigo-600 font-bold">1 hr</span>
            </div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100">
            <h3 class="text-lg font-bold text-gray-800 mb-2">Reparación de PC</h3>
            <p class="text-gray-600 text-sm mb-4">Ofrecido por: Carlos R.</p>
            <div class="flex justify-between items-center">
                <span class="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded">Tecnología</span>
                <span class="text-indigo-600 font-bold">2 hrs</span>
            </div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100">
            <h3 class="text-lg font-bold text-gray-800 mb-2">Diseño de Logo</h3>
            <p class="text-gray-600 text-sm mb-4">Ofrecido por: Ana P.</p>
            <div class="flex justify-between items-center">
                <span class="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded">Arte</span>
                <span class="text-indigo-600 font-bold">3 hrs</span>
            </div>
        </div>
    </div>
    '''
    return HttpResponse(html)
