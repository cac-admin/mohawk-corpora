class AudioFileTranscriptionEditor{
  constructor(){
    this.aft_list = []

    var self=this
    $('[x-data-model="audio_file_transcription"][x-data-action="edit"]').each(function(index,element){
      $(element).on('click', function(event){
        window.location = event.delegateTarget.attributes['x-data-url'].value
      })
    })

    $('[x-data-model="audio_file_transcription"][x-data-field]').each(function(index,element){
      $(element).on('blur', function(event){
        self.save(event.target)
      })
    })

    $('a[x-data-model="audio_file_transcription"][x-data-action="delete"]').each(function(index,element){
      $(element).on('click', function(event){
        event.preventDefault();
        var id = element.attributes['x-data-id'].value
        var name = $(`[x-data-model="audio_file_transcription"][x-data-id="${id}"][x-data-field="name"]`).get(0).attributes['x-data-value'].value

        self.create_modal(
          'Confirm Delete',
          `Are you sure you want to delete <b>${ name }</b>? This cannot be undone.`,
          'Delete',
          function(){
            self.delete(event.delegateTarget)
          })
      })
    })

    $('a[x-data-model="audio_file_transcription"][x-data-action="create"]').each(function(index,element){
      $(element).on('click', function(event){
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
    $.ajax({
        url: '/api/transcription/',
        type: 'POST',
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
    }).done(function(){
      location.reload();
    });
  }

  save(element){
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
      console.log('Saved')
    })
  }

  delete(element){
    var id = element.attributes['x-data-id'].value
    var url = '/api/transcription/'+id+'/'
    $.ajax({
      url: url,
      type: "DELETE",     
    }).done(function(){
      location.reload()
    })    
  }

  add_object(){




  }

  create_modal(heading, message, action, method){
    // Destroy all other models before making a new one.
    // $('.temporary-modal .modal').each(function(index, element){
    //   element.modal('dispose')
    // })
    $('.temporary-modal').remove();

    var element = $('<div class="temporary-modal"></div>')
    var button_class = 'primary'
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
        
        var result = method();
        if (result){
          $(elm).text("")
          $(elm).append(spinner)
        }
        
      })
      
    })

  }





}