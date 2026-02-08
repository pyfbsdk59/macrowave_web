

# Create your models here.
from django.db import models

class MacroIndicator(models.Model):
    category = models.CharField(max_length=50) # A, B, C, D, E, Score
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, default="Normal") # Safe, Warning, Danger
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.value}"


class DashboardData(models.Model):
    # 儲存完整的儀表板 Context (包含所有指標、評分、列表)
    content = models.JSONField() 
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Data Snapshot at {self.updated_at}"