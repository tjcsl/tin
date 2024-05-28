// Adapted from https://stackoverflow.com/a/11077016/11317931
function insertAtCursor(myField, myValue) {
  if (document.selection) {
    myField.focus();
    sel = document.selection.createRange();
    sel.text = myValue;
  } else if (myField.selectionStart || myField.selectionStart === 0) {
    const startPos = myField.selectionStart;
    const endPos = myField.selectionEnd;
    myField.value =
      myField.value.substring(0, startPos) +
      myValue +
      myField.value.substring(endPos, myField.value.length);
    myField.selectionStart = startPos + myValue.length;
    myField.selectionEnd = startPos + myValue.length;
  } else {
    myField.value += myValue;
  }
}

$(function () {
  if (IMGBB_API_KEY) {
    const markdownToggle = $('#id_markdown');
    const description = $('#description');
    const descriptionParent = description.parent();

    descriptionParent.css({
      position: 'relative',
    });

    const upload_overlay = $('<div>')
      .css({
        display: 'none',
        position: 'absolute',
        top: 0,
        left: 0,
        width: '92%',
        height: '100%',
        'background-color': 'rgba(0, 0, 0, 0.2)',
        'z-index': 1000,
        'text-align': 'center',
        border: '10px dashed #000',
        padding: '100px 20px 0px 20px',
        'font-size': '250%',
        'box-sizing': 'border-box',
      })
      .text('Drop to embed')
      .appendTo(descriptionParent);

    descriptionParent.on({
      dragover: function (e) {
        if (markdownToggle.prop('checked')) {
          e.preventDefault();
        }
      },
      dragenter: function (e) {
        if (markdownToggle.prop('checked')) {
          const dt = e.originalEvent.dataTransfer;
          if (dt.types.includes('Files')) {
            upload_overlay.stop().fadeIn(150);
          }
        }
      },
      drop: function (e) {
        if (markdownToggle.prop('checked')) {
          const dt = e.originalEvent.dataTransfer;
          e.preventDefault();
          if (dt && dt.files.length) {
            if (dt.files.length != 1) {
              alert('Please only upload one file at a time.');
              return;
            }

            let data = new FormData();
            data.append('key', IMGBB_API_KEY);
            data.append('image', dt.files[0]);

            $.ajax({
              url: 'https://api.imgbb.com/1/upload',
              method: 'POST',
              data: data,
              processData: false,
              contentType: false,
            }).done(function (data) {
              const name = data.data.title;
              const url = data.data.url;
              insertAtCursor(description[0], `![${name}](${url})`);
            });
          }
          upload_overlay.stop().fadeOut(150);
        }
      },
    });

    upload_overlay.on('dragleave', function () {
      upload_overlay.stop().fadeOut(150);
    });
  }
});
