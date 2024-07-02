import pycountry
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from rest_framework import serializers

from apps.jobs.choices import STATUS_CHOICES, STATUS_SCHEDULED_FOR_INTERVIEW
from apps.jobs.models import JobType


class CreateJobSerializer(serializers.Serializer):
    image = serializers.ImageField()
    title = serializers.CharField()
    salary = serializers.DecimalField(max_digits=10, decimal_places=2)
    location = serializers.ChoiceField(choices=[(country.alpha_2, country.name) for country in pycountry.countries])
    type = serializers.PrimaryKeyRelatedField(queryset=JobType.objects.all())
    requirements = serializers.ListField(child=serializers.CharField())


class JobRequirementSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    requirement = serializers.CharField()


class UpdateVacanciesSerializer(serializers.Serializer):
    image = serializers.ImageField()
    title = serializers.CharField()
    salary = serializers.DecimalField(max_digits=10, decimal_places=2)
    location = serializers.ChoiceField(choices=[(country.alpha_2, country.name) for country in pycountry.countries], )
    type = serializers.PrimaryKeyRelatedField(queryset=JobType.objects.all())
    requirements = serializers.ListField(child=JobRequirementSerializer())
    active = serializers.BooleanField()


class UpdateAppliedJobSerializer(serializers.Serializer):
    review = serializers.CharField()
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    interview_date = serializers.DateTimeField(required=False)

    def validate(self, data):
        status = data.get("status")
        interview_date = data.get("interview_date")

        if status == STATUS_SCHEDULED_FOR_INTERVIEW and not interview_date:
            raise serializers.ValidationError("Interview date is required!")

        if interview_date and interview_date < timezone.now():
            raise serializers.ValidationError("You can't schedule an interview less than the current time!")
        return data


class JobApplySerializer(serializers.Serializer):
    cv = serializers.FileField(validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])])
