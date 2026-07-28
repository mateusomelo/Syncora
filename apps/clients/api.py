from rest_framework import serializers, viewsets

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name", "phone", "email", "birth_date", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        # Client.objects (TenantManager) já filtra pelo tenant corrente —
        # a request já passou pelo TenantResolutionMiddleware antes de
        # chegar aqui, então o contextvar está setado.
        qs = Client.objects.all()
        search = self.request.query_params.get("q")
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
