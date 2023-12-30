from django.db import models

from apps.common.models import BaseModel


# Create your models here.


class Tip(BaseModel):
    title = models.CharField(max_length=255, null=True)
    description = models.TextField()
    author = models.CharField(max_length=255, null=True)
    author_image = models.ImageField(upload_to="static/tip_author", null=True)
    position = models.CharField(max_length=255, null=True, blank=True)

    @property
    def author_image_url(self):
        return self.author_image.url if self.author_image else ""

    def __str__(self):
        return self.title


class FAQType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class FAQ(BaseModel):
    question = models.CharField(max_length=255)
    type = models.ForeignKey(FAQType, on_delete=models.CASCADE, related_name="faqs", blank=True, null=True)
    answer = models.TextField()

    def __str__(self):
        return self.question
