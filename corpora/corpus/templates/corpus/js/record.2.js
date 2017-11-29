



class MyRecorder extends Player{
    constructor(target_element_selector, audio_element_id='play-audio', person_pk){
        super(target_element_selector, audio_element_id)

        this.recording = false
        this.recorder = null
        this.audioBlob = null
        this.fileName = '' 
        this.visualize = null
        this.person_pk = person_pk
        this.sampleRate = null
        this.dummy = null
        this.fd = null
        this.should_vis = true
        this.skip_button = document.getElementById('skip-button')
        this.skipped = false
        this.redo = false
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.sourceNode =   this.audioContext.createMediaElementSource(this.audio);
        this.sourceNode.connect(this.audioContext.destination)        
        this.debug = true

        var self = this

        // CREATE AND REGISTER EVENT LISTENERS
        var event = document.createEvent('Event');
        event.initEvent('myrecorder.record', true, true);
        this.event_record = event

        var event = document.createEvent('Event');
        event.initEvent('myrecorder.record.start', true, true);
        this.event_record_start = event

        var event = document.createEvent('Event');
        event.initEvent('myrecorder.record.stop', true, true);
        this.event_record_stop = event;


        $(self.record_button).on('mouseup touchup',function(){
            self.start_recording();
        });

        $(self.stop_button).on('mouseup touchup',function(){
            if (self.recording){
                self.stop_recording();
            }

            // if (!$(e.currentTarget).hasClass('disabled')){       
            //     $(self.stop_button).show()
            // }

        });

        // When audio is done playing back, revert button to initial state
        $(this.audio).bind('ended', function(){        
            $('.redo').removeClass('disabled');
            $('.save').removeClass('disabled');
        });

        // Only redo button causes audio to pause?
        var fn = function(event){
            self.logger('custom ended')
            $(self.record_button).show()
            $(self.stop_button).hide()
            if (self.redo){
                self.logger('Redone - Hiding Play')
                $(self.play_button).hide()
                self.redo = false
            }
        }
        self.audio.addEventListener('pause', fn, false)


        // event record
        // event recording started
        // event recording ended
        this.actions_element.addEventListener('myrecorder.record', function(){
            self.hide_all_buttons();
            $('.sentence-block .sentence').css('opacity', 0)
            $(self.loading_button).show()
            $('.foreground-circle.loading').addClass('clicked-circle').removeClass('unclicked-circle').show();
        })

        this.actions_element.addEventListener('myrecorder.record.start', function(){
            self.hide_all_buttons();
            $('.sentence-block .sentence').css('opacity', 1)
            $(self.stop_button).show()
            $('.foreground-circle.stop').addClass('clicked-circle').removeClass('unclicked-circle').show();

        })
        this.actions_element.addEventListener('myrecorder.record.stop', function(){
            $('.foreground-circle.stop').removeClass('clicked-circle').addClass('unclicked-circle').show();
            self.hide_all_buttons();
            $(self.play_button).show()
        })



        $(".redo").click(function(e) {
            if (!$(e.currentTarget).hasClass('disabled')){
                self.redo = true
                self.reset()
            }
        });

        $('.save').click(function(e){
            if (!$(e.currentTarget).hasClass('disabled')){       
                self.save_recording()
        }})


        $(self.skip_button).click(function(){

            if (!$(self.skip_button).hasClass('disabled')){

            // console.log('record skip')
            self.skipped = true
            
            // CHANGED
            self.reset()

            // self.audio.pause()

            // if (self.recording){
            //     self.stop_recording()
            // }

            if (self.audio.src != ''){
                self.audio.src = ''
                // delete self.audio.src
            }

            // self.audio.src = ''
            // delete self.audio.src
            // delete self.audioBlob            
            
            // $('.save').addClass('disabled');
            // $('.foreground-circle.record').removeClass('clicked-circle').addClass('unclicked-circle');
            // $('.redo').addClass('disabled');
            // $(self.record_button).show()
            // $(self.play_button).show()

            }
        })


        // Check if recorderjs supported
        if (!Recorder.isRecordingSupported()) {
            $('#recorder-container').children().remove();
            var info = $('<div class="col-lg-12 col-md-12 col-sm-12 col-xs-12" style="text-align: center;">\
                <h2>Browser Recording Not Supported</h2>\
                <p>We\'re working on alternatives - and hoping browsers support WebRTC moving forward.</p>\
                </div>');
            $('#recorder-container').append(info);
            console.log("Recorder not supported");
            return undefined;
        } else {


            if (navigator.userAgent.match('Safari')!=null
              && navigator.userAgent.match('Macintosh')!=null 
              && navigator.userAgent.match('Chrome')==null){
              
                $('#recorder-container').children().remove();
                var info = $('<div class="col-lg-12 col-md-12 col-sm-12 col-xs-12" style="text-align: center;">\
                    <h2>Browser Recording Not Supported</h2>\
                    <p>Please use Chrome or Firefox.</p>\
                    </div>');
                $('#recorder-container').append(info);
                console.log("Recorder not supported");
                return undefined;
            }

            console.log("Recorder supported");

        }



    }

    reset(){
        var self = this
        
        if (self.recording){
            self.recorder.stop();
        }
        

        if (self.audio.paused != true){
            self.audio.pause();
            window.setTimeout
        }

        // if ( $(self.stop_button).css('display')!='None' ){
        //     var pause_promise = self.audio.pause();
        //     if (pause_promise !== undefined){
        //         pause_promise.then(function(){
        //             console.log('promised for pause')
        //             $(self.play_button).hide()        

        //         })
        //     } else{
        //         console.log('Promise not defined')
        //     }
        // } else {

        // }

        $('.foreground-circle.play').addClass('unclicked-circle').removeClass('clicked-circle');
        $('.redo').addClass('disabled');
        $('.save').addClass('disabled');
        $(self.record_button).show()
        $(self.stop_button).hide()
        $(self.play_button).hide()       

    }

    create_recorder(){
        var self = this
        if (self.recorder == null){

            self.recorder = new Recorder({
                    encoderPath: '/static/bower_components/opus-recorderjs/dist/waveWorker.min.js',
                    // encoderSampleRate: self.sample_rate // THIS NEEDS TO BE THE SAMPLE RATE OF THE MICROPHONE
                }); 
            
            // Have recorder listen for when the data is available
            // This fires when recording is stopped
            self.recorder.addEventListener("dataAvailable", function(e) {

                if (self.skipped == false){
                    self.actions_element.dispatchEvent(self.event_record_stop)
                    self.audioBlob = new Blob( [e.detail], {type: 'audio/wave'});
                    self.fileName = new Date().toISOString() + ".wav";
                    self.audio.src  = URL.createObjectURL( self.audioBlob );
                    self.audio.load()
                    $(self.play_button).show()
                } else{
                    self.skipped=false
                }
                // delete self.recorder;
            });

            // THis fires when recording begins.
            self.recorder.addEventListener("streamReady", function(e) {
                self.actions_element.dispatchEvent(self.event_record_start)
                self.logger('recording started')
                self.recorder.start()
                $(self.loading_button).hide()
                $(self.record_button).show()                
                setTimeout(function(){
                    if (self.should_vis==true){
                        self.visualize = new Visualize('vis-area', self.recorder.sourceNode, self.recorder.audioContext);
                        self.visualize.start();
                    }
                }, 200);
            });
        }
    }

    start_recording(){
        var self = this
        self.actions_element.dispatchEvent(self.event_record)
        $(self.skip_button).addClass('disabled')
        if (self.recording == false) {
            // Start recorder if inactive and set recording state to true
            self.recording = true

            // Initialize audio stream (and ask the user if recording allowed?)
            // Initialize the recorder
            // Using recorderjs: https://github.com/chris-rudmin/Recorderjs
            // encoderPath option: directs to correct encoderWorker location
            // leaveStreamOpen option: allows for recording multiple times wihtout reinitializing audio stream

            // create an audio context then close it so we can detect microphpne sample rate
            // if (self.sampleRate == null){
            //     window.AudioContext = window.AudioContext || window.webkitAudioContext;
            //     self.dummy = new AudioContext();
            //     self.sample_rate = self.dummy.sampleRate;
            //     self.dummy.close();
            //     delete self.dummy;
            // }

            self.create_recorder()
            $('.foreground-circle.record').removeClass('unclicked-circle').addClass('clicked-circle');
            
            self.logger('init stream')
            $(self.loading_button).show()
            window.setTimeout(function(){
                self.recorder.initStream()
            }, 0)
        }
    }


    stop_recording(){
        var self = this
        $(this.stop_button).hide()
        $(this.play_button).show()
        if (self.should_vis==true){
            self.visualize.stop();
            // delete self.visualize;
        }
        // Stop recorder if active and set recording state to false
        this.recording = false
        this.recorder.stop()

        $('.redo').removeClass('disabled');
        $('.foreground-circle.record').removeClass('clicked-circle').addClass('unclicked-circle');

        $(self.skip_button).removeClass('disabled')
    }



    save_recording(){
        var self = this

        self.audio.pause();
        $('.redo').addClass('disabled');
        $('.save').addClass('disabled');
        $('.next').addClass('disabled');

        // Initialize FormData
        self.fd = new FormData();
        // Set enctype to multipart; necessary for audio form data
        self.fd.enctype="multipart/form-data";

        // Add audio blob as blob.wav to form data
        self.fd.append('audio_file', self.audioBlob, self.fileName);

        // Append necessary person and sentence pks to form data to add to recording model
        self.fd.append('person', self.person_pk);
        self.fd.append('sentence', sentences.sentence.id);

        self.hide_all_buttons()
        $(self.loading_button).show()

        $.ajax({

            type: 'POST',
            url: '/record/',
            data: self.fd,
            processData: false,
            contentType: false,
            success: function(data) {
                console.log("Recording data successfully submitted and saved");

                delete self.fd;
                delete self.audioBlob
                delete self.audio.src
                delete self.fileName

                self.hide_all_buttons()
                $(self.record_button).show()

                sentences.next()

            },
            error: function(xhr, ajaxOptions, thrownError) {
                // Display an error message if views return saving error
                $("#status-message h2").text("Sorry, there was an error!");
                $("#status-message").show();
                hide_loading()
            }
        });
    }    

}

