from django.db import models

from apps.core.models import TenantModel


class Client(TenantModel):
    name = models.CharField(max_length=200, verbose_name="Nome")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de nascimento")
    notes = models.TextField(blank=True, verbose_name="Observações")
    photo = models.ImageField(upload_to="clients/photos/", blank=True, null=True, verbose_name="Foto")

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

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="documents", verbose_name="Cliente"
    )
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        verbose_name="Tipo de documento",
    )
    file = models.FileField(upload_to="clients/documents/", verbose_name="Arquivo")
    description = models.CharField(max_length=255, blank=True, verbose_name="Descrição")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} · {self.client}"
