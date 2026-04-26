from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Client, Role

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'email', 'username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-full'
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        try:
            role = Role.objects.get(role_name='usuario')
            user.role = role
        except Role.DoesNotExist:
            pass
        if commit:
            user.save()
        return user

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'email', 'phone', 'biography', 'location']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-full'}),
            'email': forms.EmailInput(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-full'}),
            'phone': forms.TextInput(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-full'}),
            'biography': forms.Textarea(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-full', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-full'}),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'phone': 'Teléfono',
            'biography': 'Biografía',
            'location': 'Ubicación',
        }
