from typing import List

import pycountry
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpRequest
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.jobs.choices import STATUS_PENDING, STATUS_ACCEPTED
from apps.jobs.models import Job, JobType, AppliedJob
from apps.misc.models import Tip
from apps.notification.choices import NOTIFICATION_JOB_APPLIED
from apps.notification.models import Notification

User = get_user_model()


def get_searched_jobs(query: str, user: User) -> List[dict]:
    jobs = Job.objects.filter(
        Q(title__icontains=query) |
        Q(location__icontains=query) | Q(type__name__icontains=query) |
        Q(recruiter__company_profile__name__icontains=query), active=True).order_by('-created')

    data = [
        {
            "id": single_job.id,
            "title": single_job.title,
            "recruiter": {
                "id": single_job.recruiter.company_profile.id,
                "name": single_job.recruiter.company_profile.name,
            },
            "job_image": single_job.image_url,
            "location": pycountry.countries.get(alpha_2=single_job.location).name,
            "type": single_job.type.name,
            "salary": single_job.salary,
            "is_saved": single_job.is_saved_by_user(user),
        }
        for single_job in jobs
    ]

    return data


def job_home_data(queryset: List[Job], profile_name: str, tip: Tip, job_types: List[JobType], user: User) -> dict:
    data = {
        "profile_name": profile_name,
        "tip": {
            "id": tip.id,
            "title": tip.title,
            "author_image": tip.author_image_url
        } if tip else {},

        "job_types": [
            {
                "id": job_type.id,
                "name": job_type.name
            }
            for job_type in job_types
        ],
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "recruiter": {
                    "id": job.recruiter.company_profile.id,
                    "name": job.recruiter.company_profile.name,
                },
                "job_image": job.image_url,
                "location": pycountry.countries.get(alpha_2=job.location).name,
                "type": job.type.name,
                "salary": job.salary,
                "is_saved": job.is_saved_by_user(user)
            }
            for job in queryset
        ]
    }

    return data


def get_job_by_id(job_id: str) -> Job:
    job = Job.objects.get_or_none(id=job_id)

    if job is None:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Job with this id does not exist",
                           status_code=status.HTTP_404_NOT_FOUND)
    return job


def job_details_data(job: Job, user: User, request: HttpRequest) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "recruiter": {
            "id": job.recruiter.company_profile.id,
            "name": job.recruiter.company_profile.name,
        },
        "job_image": job.image_url,
        "location": pycountry.countries.get(alpha_2=job.location).name,
        "type": job.type.name,
        "salary": job.salary,
        "is_saved": job.is_saved_by_user(user),
        "requirements": [
            {
                "id": requirement.id,
                "requirement": requirement.requirement
            }
            for requirement in job.requirements.all()
        ],
        "url": request.build_absolute_uri()
    }


def apply_to_job(job: Job, user: User, data: dict) -> None:
    # Check if the user has already applied to the job and their application is still pending
    existing_pending_application = AppliedJob.objects.filter(job=job, user=user,
                                                             status=STATUS_PENDING).exists()
    if existing_pending_application:
        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                           err_msg="You have already applied to this job and your application is still pending.",
                           status_code=status.HTTP_409_CONFLICT)

    # Check if the user has already applied to the job and their application has been accepted
    existing_accepted_application = AppliedJob.objects.filter(job=job, user=user,
                                                              status=STATUS_ACCEPTED).exists()
    if existing_accepted_application:
        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                           err_msg="You have already applied to this job and your application has been accepted.",
                           data={}, status_code=status.HTTP_409_CONFLICT)

    # Create the applied job
    AppliedJob.objects.create(job=job, cv=data.get("cv"), user=user)

    # Create notification
    Notification.objects.create(user=user, notification_type=NOTIFICATION_JOB_APPLIED,
                                message="You have applied for a job")
