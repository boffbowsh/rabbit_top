(function($) {
  var queueTemplate;
  var queues = {data: {}};
  queues.update = function(object) {
    $.extend(this.data, object);
    $("tbody").empty();
    Object.keys(this.data).sort(function (a, b) {
      return a > b ? 1 : -1;
    }).forEach(function (queueName){
      var queue = queues.data[queueName];
      queue.etc = queue.messages / (queue.out_rate - queue.in_rate);
      $("tbody").append(queueTemplate({queue: queue}));
    });
  }

  var staticColumns = ["messages", "unacked", "consumers", "in_rate", "out_rate"]

  function initializeQueues() {
    queueTemplate = Handlebars.compile($("#queue-template").html());
    $.ajax({
      url: "queues.json",
      dataType: "json",
      success: function(data) {
        queues.update(data);
        if (!!window.EventSource) {
          var source = new EventSource('subscribe');
          source.addEventListener("message", function(e) {
            queues.update(JSON.parse(e.data));
          });
        } else {
          setTimeout(1000, initializeQueues);
        }
      }
    });
  }

  $(document).ready(initializeQueues);
})(jQuery);

Handlebars.registerHelper("etcLabel", function(etc) {
  if (etc === Infinity || etc < 0) {
    return "danger";
  } else if (etc < 1) {
    return "";
  } else if (etc < 60) {
    return "info";
  } else {
    return "warning";
  }
});

Handlebars.registerHelper("etcFormat", function(etc) {
  if (etc === Infinity || etc < 0) {
    return new Handlebars.SafeString("&infin;");
  } else {
    var time = new Date(etc*1000);
    if (isNaN(time.valueOf()) || time < 1000) {
      return "";
    } else {
      return [time.getUTCHours(),
              time.getUTCMinutes(),
              time.getUTCSeconds()].map(function (digits) {
                digits = digits.toString();
                return digits.length == 2 ? digits : "0" + digits;
              }).join(":");
    }
  }
});
