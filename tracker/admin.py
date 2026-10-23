from django.contrib import admin

from .models import Company, Interview, JobApplication, Reminder

admin.site.register(Company)
admin.site.register(JobApplication)
admin.site.register(Interview)
admin.site.register(Reminder)
