from rest_framework import serializers, viewsets

from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "duration_minutes",
            "color",
            "allowed_professionals",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return Service.objects.select_related("category").all()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
