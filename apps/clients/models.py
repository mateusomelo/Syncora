from django.db import models

from apps.core.models import TenantModel


class Client(TenantModel):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to="clients/photos/", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["tenant", "name"])]

    def __str__(self):
        return self.name


class ClientDocument(TenantModel):
    class DocumentType(models.TextChoices):
        RG = "rg", "RG"
        CPF = "cpf", "CPF"
        EXAM = "exam", "Exame"
        CONTRACT = "contract", "Contrato"
        OTHER = "other", "Outro"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(
        max_length=20, choices=DocumentType.choices, default=DocumentType.OTHER
    )
    file = models.FileField(upload_to="clients/documents/")
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} · {self.client}"
