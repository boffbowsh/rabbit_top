(function($) {
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

  function update() {
    $.ajax({
      url: "/queues.json",
      dataType: "json",
      success: function(data) {
        $("tbody").empty();
        data.sort(function (a, b) {
          return a.name > b.name ? 1 : -1;
        }).forEach(function (queue){
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
        setTimeout(update, 1000);
      }
    });
  }

  $(document).ready(update);
})(jQuery);
