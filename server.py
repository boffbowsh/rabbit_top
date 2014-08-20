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
import json, base64, functools

class Host:
  def __init__(self):
    self.queues = {}
    self.subscribers = []

    contextFactory = QueueResource.WebClientContextFactory()
    self.agent = Agent(reactor, contextFactory, pool=HTTPConnectionPool(reactor, persistent=True))

    headers = {"User-Agent": ["RabbitTop/0.1"]}
    if environ.get("RMQ_API_USER") and environ.get("RMQ_API_PASS"):
      auth = base64.b64encode("%s:%s" % (environ.get("RMQ_API_USER"), environ.get("RMQ_API_PASS")))
      headers.update({"Authorization": ["Basic %s" % auth]})
    self.headers = Headers(headers)
    self.url = "%s/api/queues/%s" % (
      environ.get("RMQ_API_URL").rstrip("/"),
      quote(environ.get("RMQ_VHOST", "/"),"")
    )

    loop = LoopingCall(self.update)
    loop.start(1, now=True)

  def cbBody(self, body):
    updatedQueues = {}

    for queue in map(self.queueMap, json.loads(body)):
      if queue["name"] in self.queues and queue == self.queues[queue["name"]]:
        pass
      else:
        updatedQueues[queue["name"]] = queue

    self.queues.update(updatedQueues)
    for subscriber in self.subscribers:
      subscriber(updatedQueues)

  def cbRequest(self, response):
    return readBody(response).addCallback(self.cbBody)

  def queueMap(self, queue):
    return {"name": queue["name"],
            "messages": queue["messages"],
            "unacked": queue["messages_unacknowledged"],
            "consumers": queue["consumers"],
            "in_rate": queue.get("message_stats",{}).get("publish_details",{}).get("rate",0),
            "out_rate": queue.get("message_stats",{}).get("deliver_get_details",{}).get("rate",0)}

  def update(self):
    d = self.agent.request("GET", self.url, self.headers)
    d.addCallback(self.cbRequest)
    return d

  def toJSON(self):
    return json.dumps(self.queues)

  def registerSubscriber(self, subscriber):
    self.subscribers.append(subscriber)

  def unregisterSubscriber(self, subscriber):
    self.subscribers.remove(subscriber)

class QueueResource(Resource):
  class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
      return ClientContextFactory.getContext(self)

  def __init__(self, host):
    self.host = host
    Resource.__init__(self)

  def render_GET(self, request):
    request.setHeader("content-type", "application/json")
    request.setResponseCode(200)
    return self.host.toJSON()

class Subscriber(Resource):
  def __init__(self, host):
    self.requests = []
    host.registerSubscriber(self.receiveUpdate)
    Resource.__init__(self)

  def render_GET(self, request):
    request.setHeader("content-type", "text/event-stream; charset=utf-8")
    request.setResponseCode(200)
    self.requests.append(request)
    return NOT_DONE_YET

  def receiveUpdate(self, data):
    for request in self.requests:
      request.write("data: %s\r\n\r\n" % json.dumps(data))

if __name__ == "__main__":
  host = Host()
  root = File(path.abspath("./public"))
  root.putChild("queues.json", QueueResource(host))
  root.putChild("subscribe", Subscriber(host))

  reactor.listenTCP(int(environ.get("PORT", 8000)), Site(root))
  reactor.run()
