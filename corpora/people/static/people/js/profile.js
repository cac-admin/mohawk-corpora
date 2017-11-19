
class Profile{
  constructor(pk, target_element_selector, target_alert_element_selector=null){
    this.base_url = '/api/persons/'+pk+'/'
    this.target_element = $(target_element_selector)
    this.alert_element = (target_alert_element_selector==null) ? null : $(target_alert_element_selector);
    this.data = null
    this.alert = null
    this.change_counter = 0
    this.saving = false
    var self = this

    // CREATE AND REGISTER EVENT LISTENERS
    var event = document.createEvent('Event');
    event.initEvent('profile.loaded', true, true);
    this.profile_loaded_event = event;


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
    
    var elem = '<div class="alert " role="alert"></div>'
    this.alert = $(elem)
    $(this.alert).hide()
    if (this.alert_element == null){
      $(this.target_element).append(this.alert)
    } else {
      $(this.alert_element).append(this.alert)
    }

    document.dispatchEvent(this.profile_loaded_event);

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
          self.initialize_elements();
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
      if (self.change_counter<=0){
        if (self.change_counter<0){self.change_counter=0}

        if (self.saving == false){  
          self.put(self.data)
        } else{
          window.setTimeout(function(){
            self.change_counter += 1
            self.save()
          }, 1000)
        }
      }
    }, 1000)

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
      $(this.alert).addClass('alert-info').html('Profile&nbsp;updated').fadeIn().delay(500).fadeOut()
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

  display(){
    this.form_element = $(this.target_element).clone()
    $(this.target_element).empty()
    this.display_element = $("<div class='row profile profile-display-element'></div>")

    if (this.data.user != null){
      this.display_element.append($('<div class="col-12 email" id="id_email"><span>Email:</span> <a target="_blank" href="mailto:'
      +this.data.user.email+'?subject=corpora.io">'+this.data.user.email+'</a></div>'))
    }
    this.display_element.append($('<div class="col-12 full_name" id="id_full_name"><span>Name:</span> '+this.data.full_name+'</div>'))

    if (this.data.demographic != null){ 
      this.display_element.append($('<div class="col-12 sex" id="id_sex"><span>Sex:</span>&nbsp;'+this.data.demographic.sex+'</div>'))
      this.display_element.append($('<div class="col-12 age" id="id_age"><span>Age:</span>&nbsp;'+this.data.demographic.age+'</div>'))
      var tribes = []
      for (var i in this.data.demographic.tribe){
        console.log(this.data.demographic.tribe[i])
        tribes.push(this.data.demographic.tribe[i].name)
      }
      this.display_element.append($('<div class="col-12 tribe" id="id_tribe"><span>Tribes:</span> '+tribes+'</div>'))
    }
    $(this.target_element).append(this.display_element)
  }


}
