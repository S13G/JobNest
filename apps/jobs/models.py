import pycountry
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse

from apps.common.models import BaseModel
from apps.jobs.managers import JobManager

User = get_user_model()


# Create your models here.

class JobType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Job(BaseModel):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.ForeignKey(JobType, on_delete=models.CASCADE, related_name="jobs")
    location = models.CharField(
        max_length=255, null=True, choices=[(country.alpha_2, country.name) for country in pycountry.countries],
    )
    active = models.BooleanField(default=True)
    is_saved = models.BooleanField(default=False)

    objects = JobManager()

    def get_absolute_url(self):
        return reverse('job-details', args=[str(self.id)])

    def is_saved_by_user(self, user):
        return self.saved_jobs.filter(user=user).exists()

    def __str__(self):
        return f"{self.recruiter.company_profile.name} > {self.title}"


class JobRequirement(BaseModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="requirements")
    requirement = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.job.title} > {self.requirement}"


class SavedJob(BaseModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_jobs")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job"], name="unique_user_job"
            )
        ]

    def __str__(self):
        return f"{self.user.email} > {self.job.title}"


class AppliedJob(BaseModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applicants")
    cv = models.FileField(
        upload_to="cv_uploads/",
        validators=[FileExtensionValidator(allowed_extensions=['doc', 'pdf', 'docx'])]
    )
    review = models.TextField(null=True, blank=True)
    waiting_for_review = models.BooleanField(default=True)
    scheduled_for_interview = models.BooleanField(default=False)
    scheduled_for_interview_date = models.DateTimeField(null=True, blank=True)
    is_accepted = models.BooleanField(null=True)

    def __str__(self):
        return f"{self.user.email} applied for {self.job.title}"
