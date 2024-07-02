from typing import List

import pycountry
from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.jobs.choices import STATUS_PENDING, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_SCHEDULED_FOR_INTERVIEW
from apps.jobs.models import Job, JobType, AppliedJob, SavedJob
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
                           status_code=status.HTTP_409_CONFLICT)

    # Check if the user has already applied for the job is scheduled for an interview
    existing_scheduled_interview = AppliedJob.objects.filter(job=job, user=user,
                                                             status=STATUS_SCHEDULED_FOR_INTERVIEW).exists()
    if existing_scheduled_interview:
        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                           err_msg="You have already applied to this job and your application has been scheduled for an interview.",
                           status_code=status.HTTP_409_CONFLICT)

    # Check if the user has already applied to the job and their application was rejected
    existing_rejected_application = AppliedJob.objects.filter(job=job, user=user, status=STATUS_REJECTED)

    if existing_rejected_application.exists():
        existing_rejected_application.update(status=STATUS_PENDING, cv=data.get("cv"))
    else:
        # Create the applied job
        AppliedJob.objects.create(job=job, cv=data.get("cv"), user=user)

    # Create notification
    Notification.objects.create(user=user, notification_type=NOTIFICATION_JOB_APPLIED,
                                message="You have applied for a job")


def get_applied_jobs(search: str) -> List[dict]:
    applied_jobs = AppliedJob.objects.filter(
        Q(job__title__icontains=search) |
        Q(job__location__icontains=search) | Q(job__type__name__icontains=search) |
        Q(job__recruiter__company_profile__name__icontains=search) |
        Q(status__icontains=search)).order_by('-created')

    data = [
        {
            "id": single_job.id,
            "title": single_job.job.title,
            "recruiter": {
                "id": single_job.job.recruiter.company_profile.id,
                "name": single_job.job.recruiter.company_profile.name,
            },
            "job_image": single_job.job.image_url,
            "status": single_job.status,
        }
        for single_job in applied_jobs
    ]

    return data


def applied_job_details_data(job_id: str, current_user: User) -> dict:
    applied_job = AppliedJob.objects.get_or_none(id=job_id, user=current_user)

    if applied_job is None:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Applied job with this id does not exist",
                           status_code=status.HTTP_404_NOT_FOUND)

    data = {
        "id": applied_job.id,
        "title": applied_job.job.title,
        "recruiter": {
            "id": applied_job.job.recruiter.company_profile.id,
            "name": applied_job.job.recruiter.company_profile.name,
        },
        "job_image": applied_job.job.image_url,
        "location": pycountry.countries.get(alpha_2=applied_job.job.location).name,
        "type": applied_job.job.type.name,
        "salary": applied_job.job.salary,
        "status": applied_job.status,
        "review": applied_job.review or "",
        "interview_date": applied_job.interview_date or "",
    }

    return data


def filter_applied_jobs_data(queryset: QuerySet) -> List[dict]:
    return [
        {
            "id": application.id,
            "title": application.job.title,
            "recruiter": {
                "id": application.job.recruiter.company_profile.id,
                "name": application.job.recruiter.company_profile.name,
            },
            "job_image": application.job.image_url,
            "status": application.status,
            "salary": application.job.salary,
            "location": pycountry.countries.get(alpha_2=application.job.location).name,
            "type": application.job.type.name,
            "review": application.review or "",
            "interview_date": application.interview_date or "",
        }
        for application in queryset
    ]


def create_saved_jobs(job: Job, current_user: User) -> dict:
    try:
        saved_job = SavedJob.objects.create(job=job, user=current_user)
    except Exception as e:
        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                           err_msg=f"Error: {e}",
                           status_code=status.HTTP_400_BAD_REQUEST)

    data = {
        "id": saved_job.id,
        "job_id": saved_job.job.id,
        "title": saved_job.job.title,
        "recruiter": {
            "id": saved_job.job.recruiter.company_profile.id,
            "name": saved_job.job.recruiter.company_profile.name,
        },
        "job_image": saved_job.job.image_url,
        "location": pycountry.countries.get(alpha_2=saved_job.job.location).name,
        "type": saved_job.job.type.name,
        "salary": saved_job.job.salary,
        "is_saved": saved_job.job.is_saved_by_user(current_user)
    }

    return data


def delete_saved_jobs(job_id: str, current_user: User):
    saved_job = SavedJob.objects.get_or_none(id=job_id, user=current_user)

    if saved_job is None:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Saved job with this id does not exist",
                           status_code=status.HTTP_404_NOT_FOUND)

    saved_job.delete()


def get_saved_jobs_data(saved_jobs: QuerySet, current_user: User) -> dict:
    data = {
        "saved_jobs": [
            {
                "id": saved_job.id,
                "job_id": saved_job.job.id,
                "title": saved_job.job.title,
                "recruiter": {
                    "id": saved_job.job.recruiter.company_profile.id,
                    "name": saved_job.job.recruiter.company_profile.name
                },
                "job_image": saved_job.job.image_url,
                "location": pycountry.countries.get(alpha_2=saved_job.job.location).name,
                "type": saved_job.job.type.name,
                "salary": saved_job.job.salary,
                "is_saved": saved_job.job.is_saved_by_user(current_user)
            }
            for saved_job in saved_jobs
        ]
    }

    return data
