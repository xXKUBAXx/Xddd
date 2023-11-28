import logging

def log_user():
    def wrapped(f):
        def wrapper(request, *args, **kwargs):
            # Log the message with user info and additional message
            try:
                email = request.user.mail
            except:
                email = "unlogged"
            logging.getLogger(__name__).info(f'{email} -> {request.path}')

            # Call the original view function
            response = f(request, *args, **kwargs)

            return response

        return wrapper

    return wrapped