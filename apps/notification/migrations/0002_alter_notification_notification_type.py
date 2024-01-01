# Generated by Django 5.0 on 2024-01-01 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('COMPLETE_PROFILE', 'Complete your profile'), ('PROFILE_UPDATED', 'Profile updated successfully'), ('JOB_APPLIED', 'You have applied for a job'), ('NEW_JOB_AVAILABLE', 'A new job has been posted'), ('APPLICATION_ACCEPTED', 'Congratulations, your application has been accepted'), ('APPLICATION_REJECTED', 'Unfortunately, your application has been rejected'), ('APPLICATION_SUBMITTED', 'Your application has been submitted and will soon be under review'), ('APPLICATION_SCHEDULED_FOR_INTERVIEW', 'Your application has been scheduled for an interview')], max_length=255),
        ),
    ]