

def extract_error_details(e: Exception) -> dict:
    error_details = {}
    # Extract additional request/response details if available
    if (request := getattr(e, "request", None)) is not None:
        error_details.update({
            "request_verb": str(request.method),
            "request_url": str(request.url),
            "request_data": str(getattr(request, "content", getattr(request, "body", None)) or "")
        })
    if (response := getattr(e, "response", None)) is not None:  # bool(response) on status errors returns False
        error_details.update({
            "server_response_status": getattr(response, "status_code", None),
            "server_response_body": str(getattr(response, "text", getattr(response, "content", None)) or "")
        })
    return error_details
