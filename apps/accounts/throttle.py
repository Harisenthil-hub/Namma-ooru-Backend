from rest_framework.throttling import UserRateThrottle

class LoginThrottle(UserRateThrottle):
    rate = '5/min'