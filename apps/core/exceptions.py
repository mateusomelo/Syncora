from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """Padroniza toda resposta de erro da API em {success, error: {code, detail}}."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    response.data = {
        "success": False,
        "error": {
            "code": response.status_code,
            "detail": response.data,
        },
    }
    return response
