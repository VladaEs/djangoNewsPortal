from django.http import QueryDict


def build_url(request, **new_parameters):
    """Return the current path with updated parameters and all other GET values."""
    query = QueryDict(mutable=True)

    # New values go first and replace values with the same name.
    for name, value in new_parameters.items():
        if value is None or value == "":
            continue
        if isinstance(value, (list, tuple)):
            query.setlist(name, [str(item) for item in value])
        else:
            query[name] = str(value)

    # Preserve every old value, including repeated parameters.
    for name, values in request.GET.lists():
        if name not in new_parameters:
            query.setlist(name, values)

    encoded_query = query.urlencode()
    if not encoded_query:
        return request.path
    return f"{request.path}?{encoded_query}"
