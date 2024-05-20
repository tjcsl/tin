$(function () {
    if (IMGBB_API_KEY) {
        const markdownToggle = $("#id_markdown");
        const description = $("#description");
        const descriptionParent = description.parent();

        descriptionParent.css({
            "position": "relative",
        })

        const upload_overlay = $("<div>").css({
            "display": "none",
            "position": "absolute",
            "top": 0,
            "left": 0,
            "width": "92%",
            "height": "100%",
            "background-color": "rgba(0, 0, 0, 0.2)",
            "z-index": 1000,
            "text-align": "center",
            "border": "10px dashed #000",
            "padding": "100px 20px 0px 20px",
            "font-size": "250%",
            "box-sizing": "border-box",
        }).text("Drop to embed").appendTo(descriptionParent);

        descriptionParent.on({
            "dragover": function (e) {
                if (markdownToggle.prop("checked")) {
                    e.preventDefault();
                }
            },
            "dragenter": function (e) {
                if (markdownToggle.prop("checked")) {
                    const dt = e.originalEvent.dataTransfer;
                    if (dt.types.includes("Files")) {
                        upload_overlay.stop().fadeIn(150);
                    }
                }
            },
            "drop": function (e) {
                if (markdownToggle.prop("checked")) {
                    const dt = e.originalEvent.dataTransfer;
                    e.preventDefault();
                    if (dt && dt.files.length) {
                        console.log(dt.files);
                        if (dt.files.length != 1) {
                            alert("Please only upload one file at a time.");
                            return;
                        }

                        let data = new FormData();
                        data.append("key", IMGBB_API_KEY);
                        data.append("image", dt.files[0]);

                        $.ajax({
                            url: "https://api.imgbb.com/1/upload",
                            method: "POST",
                            data: data,
                            processData: false,
                            contentType: false,
                        }).done(function (data) {
                            console.log(data);
                            description.val(description.val() + "\n\n![](" + data.data.url + ")");
                        });
                    }
                    upload_overlay.stop().fadeOut(150);
                }
            },
        });

        upload_overlay.on("dragleave", function () {
            upload_overlay.stop().fadeOut(150);
        });
    }
});
