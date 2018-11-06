


class TestMiddleware:
    def process_request(self,request):
        print request
        return None

    def process_response(self,request,response):
        print request,response
        return response

    def process_view(self,request,view_func,view_args,view_kwargs):
        print request,view_func, view_args,view_kwargs
        return None



