$(function () {
    if (imagekitEnabled) {
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
                console.log("dragover");
                e.preventDefault();
            },
            "dragenter": function (e) {
                console.log("dragenter");
                var dt = e.originalEvent.dataTransfer;
                if (dt.types.includes("Files")) {
                    upload_overlay.stop().fadeIn(150);
                }
            },
            "drop": function (e) {
                console.log("drop");
                var dt = e.originalEvent.dataTransfer;
                e.preventDefault();
                if (dt && dt.files.length) {
                    console.log(dt.files);
                    if (dt.files.length != 1) {
                        alert("Please only upload one file at a time.");
                        return;
                    }

                    console.log(imagekitToken);

                    imagekit.upload({
                        file: dt.files[0],
                        fileName: dt.files[0].name,
                        tags: ["tin"],
                        token: imagekitToken,
                        signature: imagekitSignature,
                        expire: imagekitExpire,
                    }).then(result => {
                        console.log(result);
                    }).then(error => {
                        console.log(error);
                    })
                }
                upload_overlay.stop().fadeOut(150);
            },
        });

        upload_overlay.on("dragleave", function () {
            upload_overlay.stop().fadeOut(150);
        });
    }
});
