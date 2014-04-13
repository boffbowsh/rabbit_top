(function($) {
  var queues = {data: {}};
  queues.update = function(object) {
    $.extend(this.data, object);
    $("tbody").empty();
    Object.keys(this.data).sort(function (a, b) {
      return a > b ? 1 : -1;
    }).forEach(function (queueName){
      var queue = queues.data[queueName];
      var row = $("<tr>");
      row.append($("<td>").text(queue.name));
      staticColumns.forEach(function(key) {
        row.append($("<td>").text(parseInt(queue[key])));
      });

      var etcEl = $("<td>");
      etcEl.html(formatTime(queue.messages / (queue.out_rate - queue.in_rate)));
      row.append(etcEl);
      $("tbody").append(row);
    });
  }

  var staticColumns = ["messages", "unacked", "consumers", "in_rate", "out_rate"]

  function formatTime(seconds) {
    if (seconds === Infinity || seconds < 0) {
      return "&infin;";
    } else {
      var time = new Date(seconds*1000);
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
  }

  function initializeQueues() {
    $.ajax({
      url: "queues.json",
      dataType: "json",
      success: function(data) {
        queues.update(data);
        if (!!window.EventSource) {
          var source = new EventSource('subscribe');
          source.addEventListener("message", function(e) {
            console.log(e.data);
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
