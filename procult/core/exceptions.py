# -*- coding: utf-8 -*-

from collections import OrderedDict

from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    print("Passou aqui")


    # Now add the HTTP status code to the response.
    if response is not None:
        response.data = {}
        errors = {}
        for field, value in exc.detail.items():
            if isinstance(value, list):
                errors[field] = value[0]
            elif isinstance(value, OrderedDict):
                _iter_errors_dict(value, errors)

        response.data['errors'] = errors
        response.data['status'] = response.status_code

    return response


def _iter_errors_dict(value, errors):
    for field, message in value.items():
        errors[field] = message[0]
