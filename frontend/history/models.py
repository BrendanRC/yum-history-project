from django.db import models

class YumHistory(models.Model):
    transaction_id = models.CharField(max_length=50)
    timestamp = models.DateTimeField()
    command = models.TextField()
    user_id = models.CharField(max_length=50, null=True, blank=True)
    package_name = models.CharField(max_length=200)
    package_version = models.CharField(max_length=100)
    package_arch = models.CharField(max_length=20)
    action = models.IntegerField()
    
    class Meta:
        db_table = 'yum_history'
