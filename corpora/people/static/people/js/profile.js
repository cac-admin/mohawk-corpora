
class Profile{
  constructor(pk, target_element_selector){
    this.base_url = '/api/persons/'+pk+'/'
    this.target_element = $(target_element_selector)
    this.data = null
    this.alert = null
    this.change_counter = 0
    this.saving = false
    var self = this
  }

  load(){
    this.get_data()
  }

  initialize_elements(){
    var self = this
    $(this.target_element).find('form').on('submit', function(event){
      event.preventDefault();
      self.save();
    });

    $(this.target_element).find('form input, form select').change(function(){
      self.change_counter += 1
      self.save()
    });
    


    var elem = '<div class="alert " role="alert" style="position:absolute; right: 0;"></div>'
    this.alert = $(elem)
    $(this.alert).hide()
    $(this.target_element).append(this.alert)

  }

  get_data(){
    var self = this;
    $.ajax({
        url: this.base_url,
        error: function(XMLHttpRequest, textStatus, errorThrown){
          console.error('No person exists.')
          // DO SOMETHING MEANINGFUL!
        }
        }).done(function(d){
          self.data = d;
          self.initialize_elements()
        }).fail(function(){
          console.error('FAILED')
          // do something usefule!
        });
  }

  save(){
    var self = this
    var demo = this.data.demographic
    demo.age = $(this.target_element).find('#id_age').val()
    demo.sex = $(this.target_element).find('#id_sex').val()

    $.each(demo, function(key, value){
      console.log(key)
      console.log(value)
      if (value == ''){
        delete demo[key];
      }
    })

    var tribe_list;
    tribe_list = $(this.target_element).find('#id_tribe').val()

    demo.tribe = []
    for (var tribe_id of tribe_list){
      name = $(this.target_element).find('#id_tribe option[value='+tribe_id+']').html()
      var json = {'name': name, 'id': tribe_id, 'pk': tribe_id}
      demo.tribe.push(json)
    }

    this.data.demographic = demo
    this.data.full_name = $(this.target_element).find('#id_full_name').val()
    
    window.setTimeout(function(){
      self.change_counter -= 1
      if (self.change_counter==0){
        if (self.saving == false){
          self.put(self.data)
        } else{
          window.setTimeout(function(){
            self.change_counter += 1
            self.save()
          }, 2000)
        }
      }
    }, 2000)

  } 


  put(data){
    var self = this
    this.saving = true

    $.each(data, function(key, value){
      if (value == null){
        delete data[key];
      }
    })


    data = JSON.stringify(data)
    $.ajax({
      type: "PUT",
      data: data,
      url: this.base_url,
      dataType: 'json',
      contentType:"application/json; charset=utf-8",
      error: function(e){
        console.error(e.responseText)
      }
    }).done(function(){
      self.saving = false
      self.show_success()
    }).fail(function(){
    })
    return true;    
  }

  show_success(){
      $(this.alert).addClass('alert-info').text('Profile updated').fadeIn().delay(500).fadeOut()
  }

  post(data){
    var self = this
    $.ajax({
      type: "POST",
      data: data,
      url: this.base_url,
      dataType: 'json',
      contentType:"application/json; charset=utf-8",
      error: function(e){
        console.error(e.responseText)
      }
    }).done(function(){
    }).fail(function(){
      console.error('POST Failed.')
    })
    return true;    
  }


}
