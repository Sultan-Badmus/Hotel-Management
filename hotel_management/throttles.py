from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstAnonRateThrottle(AnonRateThrottle):
    scope = "burst_anon"


class BurstUserRateThrottle(UserRateThrottle):
    scope = "burst_user"
