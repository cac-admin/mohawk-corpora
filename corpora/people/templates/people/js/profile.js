
class Profile{
  constructor(pk, target_element_selector, target_alert_element_selector=null){
    this.base_url = '/api/persons/'+pk+'/'
    this.target_element = $(target_element_selector)
    this.alert_element = (target_alert_element_selector==null) ? null : $(target_alert_element_selector);
    this.data = null
    this.alert = null
    this.change_counter = 0
    this.saving = false
    this.debug = true
    var self = this

    // CREATE AND REGISTER EVENT LISTENERS
    var event = document.createEvent('Event');
    event.initEvent('profile.loaded', true, true);
    this.profile_loaded_event = event;


  }

  logger(m){
    if (this.debug)
    {console.log(m)}
  }

  load(){
    this.get_data()
  }

  initialize_elements(){
    var self = this

    self.email = document.getElementById('id_email');

    try{
      self.email.addEventListener("input", function (event) {
        // Each time the user types something, we check if the
        // email field is valid.
        if (self.email.validity.valid) {
          // In case there is an error message visible, if the field
          // is valid, we remove the error message.
          // self.email.innerHTML = ""; // Reset the content of the message
          // self.email.className = "error"; // Reset the visual state of the message
          $('#id_email').removeClass('invalid')
        }
      }, false);
    }catch(e){
      self.logger(e)
    }

    $(this.target_element).find('form').on('submit', function(event){
      event.preventDefault();

      if (!self.email.validity.valid) {
        // If the field is not valid, we display a custom
        // error message.
        // error.innerHTML = "I expect an e-mail, darling!";
        // error.className = "error active";
        // And we prevent the form from being sent by canceling the event
        event.preventDefault();
      } else{
        try{self.save()}catch(e){}  
      }
      
    });

    $(this.target_element).find('form input, form select').change(function(){
      self.change_counter += 1
      self.logger('counter = '+self.change_counter)
      self.logger('Chagned')
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
        }).done(function(d){
          self.data = d;
          self.initialize_elements();
        }).fail(function(e){
          console.log(e)
          console.log('FAILED')
          // do something usefule!
        });
  }

  save(){
    var self = this
    var demo = this.data.demographic
    this.logger('Saving....')
    demo.age = $(this.target_element).find('#id_age').val()
    demo.gender = $(this.target_element).find('#id_gender').val()

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
    this.data.username = $(this.target_element).find('#id_username').val()

    if (this.data.user != null){
      this.data.user.email = $(this.target_element).find('#id_email').val()
    }
    
    this.data.profile_email = $(this.target_element).find('#id_email').val()
    this.data.receive_weekly_updates = $(this.target_element).find('#id_receive_weekly_updates').is(':checked');

    // Set Known Languages
    // Note will need to test this works when extra forms available!
    var num_forms = $('#id_known_languages-TOTAL_FORMS').val()

    var known_languages = []
    for (var i=0; i < num_forms; i++){
      var known_language = {}
      const keys = ['id', 'accent', 'dialect', 'language', 'level_of_proficiency']      
      for (var j in keys){
        var query = '#id_known_languages-'+i+'-'+keys[j]
        self.logger(query)
        known_language[keys[j]] = $(query).val()        
      } 
      this.logger(known_language)
      known_languages.push(known_language)
    }
    this.logger(known_languages)

    this.data.known_languages = known_languages

    this.data.groups = $(this.target_element).find('#id_groups').val()
    this.logger(this.data)
    window.setTimeout(function(){
      self.change_counter -= 1
      if (self.change_counter<=0){
        if (self.change_counter<0){self.change_counter=0}

        if (self.saving == false){ 
          self.logger('Trying put...')
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
    }).done(function(e){
      $(".form-text-error").hide()
      $(".form-text").show()
      $('#person_form .invalid').removeClass('invalid')

      self.logger(e)
      self.saving = false
      self.show_success()
    }).fail(function(e){
      
      self.saving = false
      $(".form-text-error").hide()
      $(".form-text").show()
      $('#person_form .invalid').removeClass('invalid')

      var errorData = e.responseJSON
      self.logger(errorData)
      $.each(errorData, function(key, value){
        if (key == 'user'){
          $.each(value, function(k, v){
            if (k=='email'){
              // $('#id_email').addClass('invalid')
              $('#id_'+k).addClass('invalid')
              console.log(v)
              $(".error-"+k).text(v.join(' '))
              $(".error-"+k).show()
              $(".form-text."+k).hide()
            }
          })
        } else{
          $('#id_'+key).addClass('invalid')
          console.log(value)
          $(".error-"+key).text(value.join(' '))
          $(".error-"+key).show()
          $(".form-text."+key).hide()
        }
      })


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
    }).done(function(){
    }).fail(function(){
      console.log('POST Failed.')
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
