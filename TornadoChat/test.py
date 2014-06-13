from tornado.httpclient import AsyncHTTPClient, HTTPClient
import tornado.utils





acli = AsyncHTTPClient()
cli = HTTPClient()



acli.fetch("http://google.com",callback)

res = cli.fetch("http://google.com")




