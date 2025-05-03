

from django.db import models

class Reestr(models.Model):
    service_id = models.IntegerField()
    revenue_type = models.TextField()
    contractor = models.TextField()
    contract_number = models.TextField()
    sign_date = models.DateField()
    subject = models.TextField()
    code = models.TextField()
    type = models.TextField()
    status = models.TextField()

    class Meta:
        db_table = 'agrements.reestr'
        managed = False
        app_label = 'reestr'