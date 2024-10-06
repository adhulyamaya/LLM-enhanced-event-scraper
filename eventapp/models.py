from django.db import models
from django.utils.translation import gettext_lazy as _

class EntitiesMaster(models.Model):
    auditorium = models.CharField(_("Auditorium"), max_length=255)
    program_name = models.CharField(_("Program Name"), max_length=255)
    date_time = models.CharField(_("Date and Time"), max_length=255)
    artists = models.JSONField(_("Artists"), default=list, blank=True)

    class Meta:
        db_table = 'entities_master'
        verbose_name = _('entity master')
        verbose_name_plural = _('entities master')

    def __str__(self):
        return f"{self.program_name} at {self.auditorium} on {self.date_time}"
