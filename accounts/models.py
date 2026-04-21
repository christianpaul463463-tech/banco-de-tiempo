from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)
    role_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbRole'

    def __str__(self):
        return self.role_name

class Client(AbstractUser):
    client_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True)
    phone = models.CharField(max_length=20, blank=True)
    biography = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Heredados de AbstractUser: first_name, last_name, email, password, username, is_staff, is_superuser, etc.

    class Meta:
        db_table = 'tbClient'

class Skill(models.Model):
    skill_id = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=100, unique=True)
    skill_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbSkill'

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100, unique=True)
    category_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbCategory'

    def __str__(self):
        return self.category_name

class Service(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('completed', 'Completado'),
    ]
    service_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField()
    estimated_time = models.DecimalField(max_digits=5, decimal_places=2)  # horas estimadas
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbService'

class TimeAccount(models.Model):
    time_account_id = models.AutoField(primary_key=True)
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='time_account')
    balance_hours = models.DecimalField(max_digits=8, decimal_places=2, default=5.00)
    total_hours_earned = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_hours_spent = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbTimeAccount'

@receiver(post_save, sender=Client)
def create_client_time_account(sender, instance, created, **kwargs):
    if created:
        TimeAccount.objects.create(client=instance)

class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    request_id = models.AutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    requester_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sent_requests')
    provider_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='received_requests')
    request_message = models.TextField(blank=True)
    requested_hours = models.DecimalField(max_digits=5, decimal_places=2)
    request_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tbRequest'

class TimeTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('transfer', 'Transferencia'),
        ('bonus', 'Bono'),
        ('deduction', 'Deducción'),
    ]
    time_transaction_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    sender_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='received_transactions')
    hours_amount = models.DecimalField(max_digits=5, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    transaction_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbTimeTransaction'

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    reviewer_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='given_reviews')
    reviewed_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.PositiveSmallIntegerField()  # 1 a 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbReview'

class Report(models.Model):
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('under_review', 'En revisión'),
        ('resolved', 'Resuelto'),
        ('dismissed', 'Desestimado'),
    ]
    report_id = models.AutoField(primary_key=True)
    reporter_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='filed_reports')
    reported_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='received_reports')
    request = models.ForeignKey(Request, on_delete=models.SET_NULL, null=True, blank=True)
    report_reason = models.CharField(max_length=200)
    report_description = models.TextField()
    report_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tbReport'
