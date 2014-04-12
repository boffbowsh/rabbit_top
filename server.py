from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.web.client import Agent, HTTPConnectionPool, readBody
from twisted.internet import reactor
from twisted.internet.ssl import ClientContextFactory
from twisted.web.http_headers import Headers

from os import environ, path
from urllib import quote
import json, base64

class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)

class QueueResource(Resource):
    def __init__(self, *args, **kwargs):
      contextFactory = WebClientContextFactory()
      self.agent = Agent(reactor, contextFactory, pool=HTTPConnectionPool(reactor, persistent=True))

      headers = {"User-Agent": ["RabbitTop/0.1"]}
      if environ.get("RMQ_API_USER") and environ.get("RMQ_API_PASS"):
        headers.update({"Authorization": ["Basic %s" % base64.b64encode("monitor:p33kab00")]})
      self.headers = Headers(headers)

      Resource.__init__(self)

    def cbBody(self, body, request):
      queues = json.loads(body)
      queueStats = map(self.queueMap, queues)
      request.write(json.dumps(queueStats))
      request.finish()

    def cbRequest(self, response, request):
      return readBody(response).addCallback(self.cbBody, request)

    def queueMap(self, queue):
      return {"name": queue["name"],
              "messages": queue["messages"],
              "unacked": queue["messages_unacknowledged"],
              "consumers": queue["consumers"],
              "in_rate": queue["message_stats"]["ack_details"]["rate"],
              "out_rate": queue["message_stats"]["publish_details"]["rate"]}

    def render_GET(self, request):
      request.setHeader("content-type", "application/json")
      urlBase = environ.get("RMQ_API_URL").rstrip("/")

      d = self.agent.request("GET",
        "%s/api/queues/%s" % (urlBase, quote(environ.get("RMQ_VHOST", "/"),"")),
        self.headers)
      d.addCallback(self.cbRequest, request)
      return NOT_DONE_YET

if __name__ == "__main__":
  root = File(path.abspath("./public"))
  root.putChild("queues.json", QueueResource())

  reactor.listenTCP(int(environ.get("PORT", 8000)), Site(root))
  reactor.run()
