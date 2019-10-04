$(function() {
  if(assignment_submit_url) {
    var upload_overlay = $("<div>").css({
      "display": "none",
      "position": "fixed",
      "top": 0,
      "left": 0,
      "bottom": 0,
      "right": 0,
      "background-color": "rgba(0, 0, 0, 0.2)",
      "z-index": 1000,
      "text-align": "center",
      "border": "10px dashed #000",
      "padding": "100px 20px 0px 20px",
      "font-size": "250%",
      "box-sizing": "border-box",
    }).text("Drop to submit").appendTo($("body"));

    $(window).on({
      "dragover": function(e) {
        e.preventDefault();
      },
      "dragenter": function(e) {
        var dt = e.originalEvent.dataTransfer;
        if(dt.types.includes("Files")) {
          upload_overlay.stop().fadeIn(150);
        }
      },
      "drop": function(e) {
        var dt = e.originalEvent.dataTransfer;
        e.preventDefault();
        if(dt && dt.files.length) {
          console.log(dt.files);
          if(dt.files.length != 1) {
            alert("Please only upload one file at a time.");
            return;
          }

          var form = $("<form>", {"action": assignment_submit_url, "method": "post", "enctype": "multipart/form-data"});
          $("<input>", {"type": "hidden", "name": "csrfmiddlewaretoken", "value": Cookies.get("csrftoken")}).appendTo(form);

          $("<input>", {"type": "file", "name": "file"}).appendTo(form).get(0).files = dt.files;

          form.css({"display": "none"});
          form.appendTo($("body"));

          form.submit();
        }
      },
    });

    upload_overlay.on("dragleave", function() {
      upload_overlay.stop().fadeOut(150);
    });
  }
});
