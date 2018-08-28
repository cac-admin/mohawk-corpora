class AudioFileTranscriptionEditor{
  constructor(){
    this.aft_list = []
    this.currentRequest = null
    var self=this
    $('[x-data-model="audio_file_transcription"][x-data-action="edit"]').each(function(index,element){
      $(element).on('click', function(event){
        event.stopPropagation();
        if (event.delegateTarget == event.target){
          window.location = event.delegateTarget.attributes['x-data-url'].value    
        }
      })
    })

    $('[x-data-model="audio_file_transcription"][x-data-action="download"]').each(function(index,element){
      $(element).on('click', function(event){
        event.stopPropagation();
        self.download(event.delegateTarget)
      })
    })    

    $('[x-data-model="audio_file_transcription"][x-data-field]').each(function(index,element){
      $(element).on('blur', function(event){
        event.stopPropagation();
        self.save(event.target)
      })
    })

    $('a[x-data-model="audio_file_transcription"][x-data-action="delete"]').each(function(index,element){
      $(element).on('click', function(event){
        event.stopPropagation();
        event.preventDefault();
        var id = element.attributes['x-data-id'].value
        var name = $(`[x-data-model="audio_file_transcription"][x-data-id="${id}"][x-data-field="name"]`).get(0).attributes['x-data-value'].value

        self.create_modal(
          'Confirm Delete',
          `Are you sure you want to delete <b>${ name }</b>? This cannot be undone.`,
          'Delete',
          function(){
            self.delete(event.delegateTarget)
            return true;
          })
      })
    })

    $('a[x-data-model="audio_file_transcription"][x-data-action="create"]').each(function(index,element){
      $(element).on('click', function(event){
        event.stopPropagation();
        event.preventDefault();


        var form =`
        <form id='file-upload' action="/api/transcription/" method="post" enctype="multipart/form-data">
          <input type="file" id="audio_file" name="audio_file" />
          <input type="hidden" name="uploaded_by" value="{{person.pk}}">
        </form>`


        
        self.create_modal(
          'Upload Audio',
          form,
          'Upload',
          function(){
            var form = $('#file-upload')[0];
            var f = document.getElementById('audio_file').files[0]
            var fd = new FormData($("#file-upload")[0]);

            if (f == undefined){
              // Need to select a file
              return false;
            } else{
              fd.append('name', f.name);
              self.create(fd)
              return true;
            }
          })
      })
    })

  }

  create(form_data){
    var self=this;
    var progress_bar = `
        <div class="progress" style="margin-top: 15px;">
          <div class="progress-bar progress-bar-striped progress-bar-animated bg-danger" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%"></div>
        </div>
`
    $('.modal-body').append(progress_bar)

    this.currentRequest = $.ajax({
        url: '/api/transcription/',
        type: 'POST',
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
        xhr: function() {
          var xhr = new window.XMLHttpRequest();
          xhr.upload.addEventListener("progress", function(evt) {
            if (evt.lengthComputable) {
                var percentComplete = parseInt(evt.loaded / evt.total * 100);
                //Do something with upload progress here
                console.log(percentComplete)
                $('.progress-bar').attr({
                  'aria-valuenow': percentComplete,
                  style: "width: "+percentComplete+"%",});

                // $(".modal-title").html('Uploading... '+percentComplete+"%")
                
            }
          }, false);
          return xhr
        },         
    }).done(function(){
      self.currentRequest=null
      window.location = '/transcriptions/'
    });
  
  }

  save(element){
    var self=this;
    var formData = new FormData();
    var id = element.attributes['x-data-id'].value
    var field = element.attributes['x-data-field'].value
    var url = '/api/transcription/'+id+'/'
    formData.append(field, $.trim($(element).text()))
    formData.enctype = "multipart/form-data"
    $.ajax({
      url: url,
      data: formData,
      type: "PUT",
      cache: false,
      contentType: false,
      processData: false,
    }).done(function(){
      self.currentRequest=null
    })
  }

  delete(element){
    var id = element.attributes['x-data-id'].value
    var url = '/api/transcription/'+id+'/'
    this.currentRequest = $.ajax({
      url: url,
      type: "DELETE",     
    }).done(function(){
      self.currentRequest=null
      location.reload()
    })    
  }

  download(element){
    var format;
    var id = element.attributes['x-data-id'].value
    try{
      format = element.attributes['x-data-format'].value
    } catch { format = 'txt'}
    var link = document.createElement("a");
    link.download = element.attributes['x-data-file-name'].value
    link.href = '/api/transcription/'+id+'.'+format;
    console.log(link.href)
    link.click();
  }

  add_object(){




  }

  create_modal(heading, message, action, method){
    // Destroy all other models before making a new one.
    // $('.temporary-modal .modal').each(function(index, element){
    //   element.modal('dispose')
    // })
    $('.temporary-modal').remove();
    var self = this;
    var element = $('<div class="temporary-modal"></div>')
    var button_class = 'danger'
    if (action.toLowerCase().search('delete')>=0){
      button_class = 'danger'
    }


    

    var template = `
<div class="modal fade bd-example-modal-sm" tabindex="-1" role="dialog" aria-labelledby="confirmAction" aria-hidden="true">
  <div class="modal-dialog ">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">${heading}</h5>

      </div>
      <div class="modal-body">
        <div id='modal-message'>${message}</div>
      </div>      
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal" >Cancel</button>
        <button type="button" class="btn btn-${button_class}" x-data-confirm="true">${action}</button>
      </div>
    </div>
  </div>
</div>
`

    $(element).append(template);
    // Add the element to the dom
    $(document.body).append(element);

    // $(element).find('#modal-message').append($(message))

    // Create the modal
    $(element).find('.modal').modal({'backdrop': 'static'})

    $(element).find('[x-data-confirm="true"]').each(function(index, elm){
      var spinner = "<i class='fas fa-circle-notch fa-spin'></i>";
      $(elm).on('click', function(){
        if (self.currentRequest == null){
          var result = method();
          if (result){
            $(elm).text("")
            $(elm).append(spinner)
          }
        }
      })
    })

    $(element).find('[data-dismiss="modal"]').each(function(index, elm){
      $(elm).on('click', function(){
        self.currentRequest.abort()
        self.currentRequest = null
      })
    })    

  }





}