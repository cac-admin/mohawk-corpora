var csrftoken = Cookies.get('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


class Sentences{

  constructor(person_id,
              content_type,
              filter_query='',
              can_approve=false,
              sentence_block_selector='.sentence-block',
              ){
    this.sentence_block = $(sentence_block_selector).get(0);
    this.objects = null
    this.sentence = null
    this.base_url = '/api/sentences/'
    this.base_quality_url = '/api/qualitycontrol/'
    this.base_sentence_url = '/api/sentences/'
    this.url_filter_query = filter_query
    this.next_url = null
    this.quality_control = {}
    this.quality_control.person = person_id
    this.can_approve = can_approve
    this.quality_control.content_type = content_type
    $(this.sentence_block).fadeOut(0);

    var self=this;
    $(this.sentence_block).find('.good').off().on('click', function(e){
      if (!$(e.currentTarget).hasClass('disabled')){
        $(this.sentence_block).find('a').addClass('disabled')
        self.up_vote();
      }
    })   

    $(this.sentence_block).find('.bad').off().on('click', function(e){
      if (!$(e.currentTarget).hasClass('disabled')){
        $(this.sentence_block).find('a').addClass('disabled')
        self.down_vote();
      }
    })

    $(this.sentence_block).find('.next').off().on('click', function(e){
      if (!$(e.currentTarget).hasClass('disabled')){
        $(this.sentence_block).find('a').addClass('disabled')
        self.next();
      }
    })    

    $(this.sentence_block).find('.approve').off().on('click', function(e){
      if (!$(e.currentTarget).hasClass('disabled')){
        $(this.sentence_block).find('a').addClass('disabled')
        self.approve();
      }
    })


    $('#confirmDelete').on('click', function(e){
      // $(e.currentTarget).addClass('disabled').off()
      $('#askDelete').modal('hide')
      self.delete_sentence();
    })

  }

  get_sentences(){
    var self = this;
    console.log('Fetching more sentences')
    $.ajax({
        url: ((this.next_url==null) ? this.base_url : this.next_url)+this.url_filter_query
        }).done(function(d){
          self.objects = d.results
          self.next_url = d.next
          if (self.objects.length == 0){
            console.log('No more sentences')
            self.all_done()
          }
          else{
            self.next()
          }
    })
  }

  reload(){
    var self = this
    $.ajax({
        url: this.base_sentence_url+this.sentence.id+'/'
        }).done(function(d){
          console.log(d)
          self.sentence.quality_control = d.quality_control
          self.sentence = d
          self.show_next_sentence()
    })    
  }

  next(){
    if (this.objects == null || this.objects.length==0){
      this.get_sentences()
    } else{
      this.sentence = this.objects.shift()
      this.show_next_sentence()
    }
  }

  all_done(){
    $(this.sentence_block).text('All done.')
    $(this.sentence_block).fadeIn('disabled')
  }

  show_next_sentence(){
    var self = this;
    if (this.sentence){
      $(this.sentence_block).removeClass('disabled')
      $(this.sentence_block).find('.approve, .good, .bad, .delete, .next').removeClass('disabled')

      $(this.sentence_block).find('a').blur()
      $(this.sentence_block).find('.sentence .text-area').remove()
      if (this.can_approve){
        var input_elm = $('<textarea id="editText" class="text-area" type="textarea" name="text" rows="3">')
      } else {
        var input_elm = $('<span class="text-area"></span>')
      }
      
      $(input_elm).val(this.sentence.text);
      $(input_elm).text(this.sentence.text);
      $(this.sentence_block).find('.sentence').append(input_elm)
      $(this.sentence_block).fadeIn('fast');


      $(input_elm).off().on('change', function(){
        self.edit_sentence()
      })

      $(input_elm).off().on('keyup', function(event){
        self.check_sentence_changed(event)
      })

    }
  }

  check_sentence_changed(event){
    if ($(event.currentTarget).val() != this.sentence.text){
      this.edit_sentence()
    }
  }

  edit_sentence(){
    var self = this
    $(this.sentence_block).find('.approve, .good, .bad').addClass('disabled')
    $(this.sentence_block).find('.save').removeClass('off').removeClass('disabled')
    $(this.sentence_block).find('.save').off().on('click', function(e){
        $(self.sentence_block).find('a').addClass('disabled')
        $(self.sentence_block).find('.save').off()
        self.save_sentence( $($('#editText').get(0)).val() );
    })     
  }

  post_qc(data){
    var self = this
    this.quality_control.object_id = this.sentence.id
    $.ajax({
      type: "POST",
      data: this.quality_control,
      url: this.base_quality_url,
      dataType: 'json',
      error: function(XMLHttpRequest, textStatus, errorThrown){
        console.log(XMLHttpRequest.status)
        console.log(XMLHttpRequest.responseText)
      }
    }).done(function(){
      self.next();
    }).fail(function(){
      console.log('Failed.')
    })
    return true;    
  }

  put_qc(data){
    var self = this
    $.ajax({
      type: "PUT",
      data: data,
      url: this.base_quality_url+this.quality_control_id+'/',
      dataType: 'json',
      error: function(e){
        console.log(e.responseText)
      }
    }).done(function(){
      self.next();
    }).fail(function(){
      console.log('Failed.')
    })
    return true;    
  }

  save_sentence(text){

    var self=this
    var data = this.sentence
    delete data.quality_control
    data.text = text
    console.log(data)
    $.ajax({
      type: "PUT",
      data: this.sentence,
      url: this.base_sentence_url+this.sentence.id+'/',
      dataType: 'json',
      error: function(XMLHttpRequest, textStatus, errorThrown){
        console.log(textStatus.responseText)
        console.log(XMLHttpRequest)
        console.log(errorThrown)
      }
    }).done(function(){
      console.log('Saved')
      self.reload();
    }).fail(function(){
      console.log('Failed.')
    })
  }

  post_put(){
    var method = 'POST'
    this.quality_control.object_id = this.sentence.id

    for (let qc of this.sentence.quality_control){
      if (qc.person == this.quality_control.person){
        console.log('Found matching qc ')
        this.quality_control_id = qc.id
        this.quality_control.bad += qc.bad
        this.quality_control.good += qc.good
        method = 'PUT'
      } else{
        
      }
    }

    if (method=='POST'){
      this.post_qc(this.quality_control)
    } else {
      this.put_qc(this.quality_control)
    }

  }

  approve(){
    this.quality_control.approved = true;
    this.quality_control.good = 0
    this.quality_control.bad = 0    
    this.quality_control.approved_by = this.person_id;
    console.log(this.quality_control);
    this.post_put();
  }
  up_vote(){
    this.quality_control.good = 1
    this.quality_control.bad = 0
    console.log(this.quality_control);
    this.post_put();
  }

  down_vote(){
    this.quality_control.bad = 1
    this.quality_control.good = 0
    console.log(this.quality_control);
    this.post_put();
  }

  delete_sentence(){
    console.log('Deleting "'+this.sentence.text+'"')
    console.log('Sentence ID: '+this.sentence.id)
    var self = this;
    $.ajax({
      type: "DELETE",
      url: this.base_sentence_url+this.sentence.id+'/',
      dataType: 'json',
      error: function(XMLHttpRequest, textStatus, errorThrown){
        console.log(textStatus.responseText)
        console.log(XMLHttpRequest)
        console.log(errorThrown)
      },
    }).done(function(){
      console.log('Deleted')
      self.next();
    }).fail(function(){
      console.log('Failed.')
    })

  }

}