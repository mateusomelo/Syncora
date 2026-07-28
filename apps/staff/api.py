from rest_framework import serializers, viewsets

from .models import Professional


class ProfessionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professional
        fields = ["id", "name", "specialties", "commission_rate", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProfessionalViewSet(viewsets.ModelViewSet):
    serializer_class = ProfessionalSerializer

    def get_queryset(self):
        return Professional.objects.all()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
