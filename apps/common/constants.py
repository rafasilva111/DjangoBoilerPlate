
from os import environ

## Websocket

WEBSOCKET_HOST = environ.get('WEBSOCKET_HOST','127.0.0.1:8000')


"""

    Management Accounts

"""

AUTOMATION_ACCOUNT = 'Automation'

AUTOMATION_ACCOUNT_DEFAULT_USER_PASSWORD = environ.get('AUTOMATION_ACCOUNT_DEFAULT_USER_PASSWORD','password')


"""

    Testing Accounts

"""

TESTING_ACCOUNT_A = 'a'

TESTING_ACCOUNT_A_PASSWORD = environ.get('TESTING_ACCOUNT_A','a')

TESTING_ACCOUNT_B = 'b'

TESTING_ACCOUNT_B_PASSWORD = environ.get('TESTING_ACCOUNT_B','b')

TESTING_ACCOUNT_C = 'c'

TESTING_ACCOUNT_C_PASSWORD = environ.get('TESTING_ACCOUNT_C','c')


