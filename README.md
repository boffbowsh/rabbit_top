# Rabbit Top

A simple way of visualising the current status of your RabbitMQ workloads. Best
suited to workflows where RabbitMQ is used as a queue for background processing
of long running jobs over a fairly constant set of queues.

The tool will display all queues in a table each with the number of messages,
number of consumers, in and out rates and also an estimated time of completion
based on the current message count and rates.

## Usage

If your RabbitMQ management interface is available to the internet, the easiest
way of deploying the tool is with [Heroku]. Substitute your API configuration as
necessary.

```bash
git clone https://github.com/boffbowsh/rabbit_top.git
heroku create --region us # Or eu if AWS Ireland is closer

# Needs custom FFI-enabled buildpack to speak to Management APIs protected by SSL
heroku config:add BUILDPACK_URL=https://github.com/kennethjiang/heroku-buildpack-python-libffi.git

heroku config:add RMQ_API_URL=https://rbt-mgmt.example.com
heroku config:add RMQ_API_USER=monitoring
heroku config:add RMQ_API_PASS=password
heroku config:add RMQ_VHOST=my_vhost # Optional, defaults to the default vhost "/"

git push heroku master
```

If you want to deploy behind your firewall, ensure you have Python's `pip` and
`setuptools` installed, then run:

```bash
pip install -r requirements.txt
```

You may want to run this inside a [virtualenv].

You'll want to supply the configuration parameters as Environment variables as
in the Heroku instructions above. This can be done in an init.d script or in a
`.env` file, which [foreman] will automatically read along with the included
`Procfile`. By default it will listen on port `8000` but this can be changed
with the `PORT` environment variable.

## Contributing

Contributions are very welcome, especially from people who want to make this
prettier. Please submit a pull request.

[Heroku]: https://heroku.com/
[virtualenv]: https://pypi.python.org/pypi/virtualenv
[foreman]: https://github.com/ddollar/foreman
