from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.web.client import Agent, HTTPConnectionPool, readBody
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.ssl import ClientContextFactory
from twisted.web.http_headers import Headers

from os import environ, path
from urllib import quote
import json, base64

class Host:
  def __init__(self):
    self.queues = []

    contextFactory = QueueResource.WebClientContextFactory()
    self.agent = Agent(reactor, contextFactory, pool=HTTPConnectionPool(reactor, persistent=True))

    headers = {"User-Agent": ["RabbitTop/0.1"]}
    if environ.get("RMQ_API_USER") and environ.get("RMQ_API_PASS"):
      headers.update({"Authorization": ["Basic %s" % base64.b64encode("monitor:p33kab00")]})
    self.headers = Headers(headers)
    self.url = "%s/api/queues/%s" % (
      environ.get("RMQ_API_URL").rstrip("/"),
      quote(environ.get("RMQ_VHOST", "/"),"")
    )

    loop = LoopingCall(self.update)
    loop.start(1, now=True)

  def cbBody(self, body):
    self.queues = map(self.queueMap, json.loads(body))

  def cbRequest(self, response):
    return readBody(response).addCallback(self.cbBody)

  def queueMap(self, queue):
    return {"name": queue["name"],
            "messages": queue["messages"],
            "unacked": queue["messages_unacknowledged"],
            "consumers": queue["consumers"],
            "in_rate": queue["message_stats"]["publish_details"]["rate"],
            "out_rate": queue["message_stats"]["ack_details"]["rate"]}

  def update(self):
    d = self.agent.request("GET", self.url, self.headers)
    d.addCallback(self.cbRequest)
    return d

  def toJSON(self):
    return json.dumps(self.queues)

class QueueResource(Resource):
  class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
      return ClientContextFactory.getContext(self)

  def __init__(self, host):
    self.host = host
    Resource.__init__(self)

  def render_GET(self, request):
    request.setHeader("content-type", "application/json")
    return self.host.toJSON()

if __name__ == "__main__":
  host = Host()
  root = File(path.abspath("./public"))
  root.putChild("queues.json", QueueResource(host))

  reactor.listenTCP(int(environ.get("PORT", 8000)), Site(root))
  reactor.run()
