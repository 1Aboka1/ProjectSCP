# myapp/middleware.py
class PrintRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("=== Incoming request ===")
        print("Method:", request.method)
        print("Path:", request.path)
        print("Headers:", request.headers)
        print("Body:", request.body.decode() if request.body else "<empty>")
        response = self.get_response(request)
        return response
