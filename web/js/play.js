// Set the name of the hidden property and the change event for visibility
var hidden, visibilityChange;
if (typeof document.hidden !== "undefined") { // Opera 12.10 and Firefox 18 and later support
  hidden = "hidden";
  visibilityChange = "visibilitychange";
} else if (typeof document.mozHidden !== "undefined") {
  hidden = "mozHidden";
  visibilityChange = "mozvisibilitychange";
} else if (typeof document.msHidden !== "undefined") {
  hidden = "msHidden";
  visibilityChange = "msvisibilitychange";
} else if (typeof document.webkitHidden !== "undefined") {
  hidden = "webkitHidden";
  visibilityChange = "webkitvisibilitychange";
}

$(function() {
  var startDate = moment();
  var duration = moment.duration();
  var endDate = null;
  var $timer = $('#timetext');
  var interval = setInterval(update, 1000);
  $('.doneButton').on('click', done);

  function zeroFill(num) {
    if (num > 9) {
      return num + "";
    }

    return "0" + num;
  }

  function formatDuration(d) {
    var seconds = zeroFill(d.seconds());
    var minutes = zeroFill(d.minutes());
    var hours = zeroFill(Math.floor(d.asHours()));

    return hours + ":" + minutes + ":" + seconds;
  }

  function update() {
    duration.add(1, 's');

    var timeString = formatDuration(duration);

    $timer.text(timeString);
  }

  function done() {
    endDate = moment();
    clearInterval(interval);
    $(".pizza").remove();
    $(".doneButton").addClass("invisible");
    $(".afterGame").removeClass("invisible");
  }

  function triedToHide() {
    if (!endDate) {
      // Still playing
      alert("No. You are still playing Pizza Blaster.");
    }
  }

  $(window).on('blur', triedToHide);

  $(document).on(visibilityChange, function() {
    if (!endDate) {
      if (document[hidden]) {
        console.log("stopping");
        clearInterval(interval);
        interval = null;
      } else if (!interval) {
        console.log("starting");
        interval = setInterval(update, 1000);
      }
    }
  });

  $('.scoreInput').on('submit', function(e) {
    var input = moment.duration($('input[name=score]').val());

    if (input - duration > 10000) {
      var confirmed = confirm("Are you sure you looked at the pizza for " + formatDuration(input) + "?");

      if (!confirmed) {
        e.preventDefault();
        return;
      }
    }

    $("input[name=real_score]").val(Math.floor(duration.asSeconds()));
    $("input[name=input_score]").val(Math.floor(input.asSeconds()));
  });

});
