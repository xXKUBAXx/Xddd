import logging

def log_user():
    def wrapped(f):
        def wrapper(request, *args, **kwargs):
            # Log the message with user info and additional message
            logging.getLogger(__name__).info(f'{request.user.email} -> {request.path}')

            # Call the original view function
            response = f(request, *args, **kwargs)

            return response

        return wrapper

    return wrapped