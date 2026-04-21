def success_response(data=None, message="OK", status=200):
    return {
        "status": "success",
        "message": message,
        "data": data
    }, status


def error_response(message="Error", status=400):
    return {
        "status": "error",
        "message": message
    }, status
