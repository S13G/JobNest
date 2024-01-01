from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    text = serializers.CharField(required=True)

    def validate(self, attrs):
        if not attrs.get("text"):
            raise serializers.ValidationError({"text": "This field is required."})
        return attrs
