class Player {
  constructor(target_element_selector){
    this.actions_element = $(target_element_selector)
    this.play_button_selector = '#play-button'
    this.stop_button_selector = '#stop-button'
    this.audio_selector = '#play-audio'
    this.audio = document.getElementById('play-audio');

    var self = this;

    $(this.play_button_selector).on('mousedown', function(){
      $('.foreground-circle.play').removeClass('unclicked-circle').addClass('clicked-circle');
      $(self.play_button_selector).on('blur', function(){
        $('.foreground-circle.play').addClass('unclicked-circle').removeClass('clicked-circle');
      });

    });
    
    $(this.play_button_selector).click(function(){
      self.audio.play();
    });    

    $(this.stop_button_selector).click(function(){
      self.audio.pause();
    });  

    // When audio is done playing back, revert button to initial state
    $(this.audio).bind('ended', function(){
      $('.foreground-circle.play').removeClass('clicked-circle').addClass('unclicked-circle');
    });

    $('a.auto-play').click(function(event){
      var obj = event.currentTarget
      console.log('auto play clicked')
      if ($(obj).hasClass('auto-play-off')){
        $(obj).removeClass('auto-play-off')
        $(obj).addClass('auto-play-on')
        self.audio.autoplay=true;
        if (self.audio.paused){
          self.audio.play()
        }
      } else {
        self.audio.autoplay=false;
        $(obj).removeClass('auto-play-on')
        $(obj).addClass('auto-play-off')
      }

    })

    $(this.audio).bind('loadstart', function(){
      $('.circle-button-container a').hide();
      $('.circle-button-container').find('.loading').show()
    });

    $(this.audio).bind('emptied', function(){
      $('.circle-button-container a').hide();
    });

    $(this.audio).bind('loadeddata', function(){
      $('.circle-button-container a').hide();
      if ($('a.auto-play').hasClass('auto-play-on')){
        self.audio.play();
      } else if (self.audio.src != null){
        $('.circle-button-container').find('.play').show()
      }
    });

    $(this.audio).bind('play', function(){
      $('.circle-button-container a').hide();
      $('.circle-button-container').find('.loading').show();
      $('.foreground-circle.loading').addClass('clicked-circle').removeClass('unclicked-circle').show();  
    });

    $(this.audio).bind('playing', function(){
      $('.circle-button-container a').hide();
      $('.foreground-circle.loading').removeClass('clicked-circle').addClass('unclicked-circle')
      $('.foreground-circle.stop').addClass('clicked-circle').removeClass('unclicked-circle')
      $('.circle-button-container').find('.stop').show()
    });

    $(this.audio).bind('pause', function(){
      $('.circle-button-container a').hide();
      $('.foreground-circle.play').removeClass('clicked-circle').addClass('unclicked-circle');
      $('.circle-button-container').find('.play').show()
      self.audio.currentTime = 0; 
    });

    $(this.audio).bind('ended', function(){
      $('.circle-button-container a').hide();
      $('.foreground-circle.play').removeClass('clicked-circle').addClass('unclicked-circle');
      $('.circle-button-container').find('.play').show()
      $(self.actions_element).find('.approve, .good, .bad').removeClass('disabled')
    });

  }

}