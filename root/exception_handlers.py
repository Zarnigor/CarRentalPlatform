from rest_framework.views import exception_handler
from rest_framework.response import Response
from root.exceptions import AppError

def app_exception_handler(exc, context):
    if isinstance(exc, AppError):
        return Response(exc.to_dict(), status=exc.status_code)
    return exception_handler(exc, context)