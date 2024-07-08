from django.db import models
from django.db.models import Avg, F
from django.utils import timezone

class Vendor(models.Model):
    name = models.CharField(max_length=255)
    contact_details = models.TextField()
    address = models.TextField()
    vendor_code = models.CharField(max_length=50, unique=True)
    on_time_delivery_rate = models.FloatField(default=0)
    quality_rating_avg = models.FloatField(default=0)
    average_response_time = models.FloatField(default=0)
    fulfillment_rate = models.FloatField(default=0)

    def __str__(self):
        return self.name

    def update_performance_metrics(self):
        completed_pos = self.purchase_orders.filter(status='completed')
        total_completed_pos = completed_pos.count()
        total_pos = self.purchase_orders.count()

        if total_completed_pos > 0:
            # On-Time Delivery Rate
            on_time_deliveries = completed_pos.filter(delivery_date__lte=F('acknowledgment_date')).count()
            self.on_time_delivery_rate = (on_time_deliveries / total_completed_pos) * 100

            # Quality Rating Average
            quality_ratings = completed_pos.exclude(quality_rating__isnull=True)
            if quality_ratings.exists():
                self.quality_rating_avg = quality_ratings.aggregate(Avg('quality_rating'))['quality_rating__avg']

        # Average Response Time
        acknowledged_pos = self.purchase_orders.exclude(acknowledgment_date__isnull=True)
        if acknowledged_pos.exists():
            avg_response_time = acknowledged_pos.annotate(
                response_time=F('acknowledgment_date') - F('issue_date')
            ).aggregate(Avg('response_time'))['response_time__avg']
            self.average_response_time = avg_response_time.total_seconds() / 3600 if avg_response_time else 0

        # Fulfilment Rate
        if total_pos > 0:
            fulfilled_pos = completed_pos.filter(issues__isnull=True).count()
            self.fulfillment_rate = (fulfilled_pos / total_pos) * 100

        self.save()

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    order_date = models.DateTimeField()
    delivery_date = models.DateTimeField()
    items = models.JSONField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    quality_rating = models.FloatField(null=True, blank=True)
    issue_date = models.DateTimeField()
    acknowledgment_date = models.DateTimeField(null=True, blank=True)
    
    issues = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"PO {self.po_number} for {self.vendor.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None if is_new else PurchaseOrder.objects.get(pk=self.pk).status
        
        super().save(*args, **kwargs)

        if is_new or self.status != old_status or (self.status == 'completed' and self.quality_rating is not None):
            self.vendor.update_performance_metrics()
            
    def acknowledge(self):
        if not self.acknowledgment_date:
            self.acknowledgment_date = timezone.now()
            self.save()

class HistoricalPerformance(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='historical_performances')
    date = models.DateTimeField(default=timezone.now)
    on_time_delivery_rate = models.FloatField()
    quality_rating_avg = models.FloatField()
    average_response_time = models.FloatField()
    fulfillment_rate = models.FloatField()

    def __str__(self):
        return f"Performance record for {self.vendor.name} on {self.date}"

    @classmethod
    def create_historical_performance(cls, vendor):
        return cls.objects.create(
            vendor=vendor,
            on_time_delivery_rate=vendor.on_time_delivery_rate,
            quality_rating_avg=vendor.quality_rating_avg,
            average_response_time=vendor.average_response_time,
            fulfillment_rate=vendor.fulfillment_rate
        )