class Error(Exception):
    pass

class UnauthorizedError(Error):
    """Exception raised for unauthorized access to alpaca servers

    Attributes:
        status_code -- status code of the HTTP response object
        alpaca_message -- content of the HTTP response that alpaca returns
        message -- explanation of the error
    """

    def __init__(self, status_code, alpaca_message):
        self.status_code = status_code
        self.alpaca_message = alpaca_message
        self.message = "Unathorized access to alpaca servers, make sure your keys are up to date and accurate"

class PageNotFoundError(Error):
    """Exception raised for attempting to access an unkown page from alpaca

    Attributes:
        status_code -- status code of the HTTP response object
        alpaca_message -- content of the HTTP response that alpaca returns
        message -- explanation of the error
    """

    def __init__(self, status_code, alpaca_message):
        self.status_code = status_code
        self.alpaca_message = alpaca_message
        self.message = "Page not found, make sure the url is accurate and free of typos"

class BadRequestError(Error):
    """Exception raised for a bad request sent to the alpaca servers

    Attributes:
        status_code -- status code of the HTTP response object
        alpaca_message -- content of the HTTP response that alpaca returns
        message -- explanation of the error
    """

    def __init__(self, status_code, alpaca_message):
        self.status_code = status_code
        self.alpaca_message = alpaca_message
        self.message = "Bad request, usually caused by the json input data being misaligned with the docs. Make sure the types of all the feilds are accurate"

class UnprocessableError(Error):
    """Exception raised for a unprocessable request sent to the alpaca servers

    Attributes:
        status_code -- status code of the HTTP response object
        alpaca_message -- content of the HTTP response that alpaca returns
        message -- explanation of the error
    """

    def __init__(self, status_code, alpaca_message):
        self.status_code = status_code
        self.alpaca_message = alpaca_message
        self.message = "Unprocessable entity, usually caused by using the wrong data field in a POST request, try changing params/json/data to one of the others"

class TooManyRequestsError(Error):
    """Exception raised for reaching the request limits on alpaca

    Attributes:
        status_code -- status code of the HTTP response object
        alpaca_message -- content of the HTTP response that alpaca returns
        message -- explanation of the error
    """

    def __init__(self, status_code, alpaca_message):
        self.status_code = status_code
        self.alpaca_message = alpaca_message
        self.message = "Too many requests. You have met your alpaca quota for requests, try slowing down a bit."

class GeneralAlpacaError(Error):
    """Exception raised for a general alpaca error

    Attributes:
        status_code -- status code of the HTTP response object
        alpaca_message -- content of the HTTP response that alpaca returns
        message -- explanation of the error
    """

    def __init__(self, status_code, alpaca_message):
        self.status_code = status_code
        self.alpaca_message = alpaca_message
        self.message = "General Alpaca Error. Alpaca returned an error not predefined in our errors."

def handle_errors(response):
    if response.status_code == 403:
        raise UnauthorizedError(response.status_code, response.content)
    elif response.status_code == 404:
        raise PageNotFoundError(response.status_code, response.content)
    elif response.status_code == 422:
        raise UnprocessableError(response.status_code, response.content)
    elif response.status_code == 429:
        raise TooManyRequestsError(response.status_code, response.content)
    else:
        raise GeneralAlpacaError(response.status_code, response.content)