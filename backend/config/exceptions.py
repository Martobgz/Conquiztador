from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Wrap every DRF error in a single {"errors": {...}} envelope.

    Keeps one error shape across all endpoints: field name -> list of messages,
    with non-field problems reported under "detail".
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict):
        response.data = {"errors": {key: _as_messages(value) for key, value in data.items()}}
    else:
        response.data = {"errors": {"detail": _as_messages(data)}}
    return response


def _as_messages(value):
    if isinstance(value, dict):
        return {key: _as_messages(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]
