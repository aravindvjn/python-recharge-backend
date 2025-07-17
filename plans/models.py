from django.db import models

class Provider(models.Model):
    title = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Plans(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='plans')
    title = models.CharField(max_length=200)
    description = models.TextField()
    validity = models.IntegerField(help_text='Validity in days')
    is_active = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    identifier = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Plans'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.provider.title} - {self.title}"
