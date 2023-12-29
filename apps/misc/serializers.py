from rest_framework import serializers as sr


class TipSerializer(sr.Serializer):
    id = sr.UUIDField()
    title = sr.CharField()
    description = sr.CharField()
    author = sr.CharField()
    author_image = sr.SerializerMethodField()
    position = sr.CharField()

    @staticmethod
    def get_author_image(obj):
        return obj.author_image.url if obj.author_image else ""

    def to_representation(self, instance):
        data = super().to_representation(instance)

        for field_name, field_value in data.items():
            if field_value is None:
                data[field_name] = ""

        return data
