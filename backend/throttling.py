from rest_framework.throttling import SimpleRateThrottle
import json


class WriteZapleczaThrottle(SimpleRateThrottle):
    scope = 'write-zaplecza'

    def get_cache_key(self, request):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else: 
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope, 
            'ident': ident
        }



    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        if request.user.account.premium_user:
            return True
        
        self.get_history(request)
        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        
        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return self.throttle_success(request)


    def get_history(self, request):
        self.key = self.get_cache_key(request)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()


    def add_timestamp(self):
        self.history.insert(0, self.now)
        self.cache.set(self.key, self.history, self.duration)

    def throttle_success(self, request):
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        categories, a = json.loads(request.data.get('categories')), int(request.data.get('a_num'))

        for _ in range(len(categories*a)):
            self.add_timestamp()
        return True