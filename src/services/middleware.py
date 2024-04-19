# class CustomHeaderMiddleware(BaseHTTPMiddleware):
#     def __init__(self, app):
#         super().__init__(app)
#         self.session = get_session()

#     async def dispatch(self, request, call_next):
#         request.headers["my_var"] = "my_value"
#         response = await call_next(request)
#         return response


@app.middleware("http")
async def add_user_privilieges_to_header(request, call_next):
    headers = dict(request.scope['headers'])
    headers[b'my_var'] = b'my custom header'
    headers[b'owned_projects'] = b"1 2 3 555554 5"
    request.scope['headers'] = [(k, v) for k, v in headers.items()]
    response = await call_next(request)
    return response



@app.get("/{some_str}")
async def root(some_str: str, some_query: str, request: Request):
    my_var = request.headers["my_var"]
    owned = request.headers["owned_projects"]
    owned_list = owned.split()
    int_list = [int(x) for x in owned_list]
    
    return {"some_str": some_str, "some_quer": some_query,
            "my_var": my_var, "owned_projects": int_list}
    

