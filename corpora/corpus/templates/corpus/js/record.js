var audio = document.getElementById('play-audio');
var recorder
var audioBlob, fileName;


function show_loading(){
    console.log('showing loading?')
    $('.circle-button-container a').hide();
    $('.circle-button-container').find('.loading').show()
    $('.sentence-block .sentence').css('opacity', .5)
}

function hide_loading(){
    $('.circle-button-container a').hide();
    $('.circle-button-container').find('.loading').hide()
    $('.sentence-block .sentence').css('opacity', 1)
}

$(document).ready(function() {
    if ( sessionStorage.getItem('reload') == "true") {
        sessionStorage.setItem('reload', "false");
        $("#status-message h2").text("Thank you for submitting a recording! Here's another sentence for you:");
        $("#status-message").show();
    }
});

// Check if recorderjs supported
if (!Recorder.isRecordingSupported()) {
    $('#recorder-container').children().remove();
    var info = $('<div class="col-lg-12 col-md-12 col-sm-12 col-xs-12" style="text-align: center;">\
        <h2>Browser Recording Not Supported</h2>\
        <p>We\'re working on alternatives - and hoping browsers support WebRTC moving forward.</p>\
        </div>');
    $('#recorder-container').append(info);
    console.log("Recorder not supported");
} else {
    console.log("Recorder supported");

    // Initialize the recorder
    // Using recorderjs: https://github.com/chris-rudmin/Recorderjs
    // encoderPath option: directs to correct encoderWorker location
    // leaveStreamOpen option: allows for recording multiple times wihtout reinitializing audio stream

    // create an audio context then close it so we can detect microphpne sample rate
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    a = new AudioContext();
    // var dummy_ac = new AudioContext();
    var sample_rate = a.sampleRate;
    console.log(sample_rate)
    a.close();
    
    var recording = false;
    // Record or halt recording when pressing record button
    $('#record-button').click(function() {
        console.log('record button pressed')
        show_loading();
        if (recording == false) {
            
            // Start recorder if inactive and set recording state to true
            recording = true

            // Initialize audio stream (and ask the user if recording allowed?)
            if (!recorder){
                recorder = new Recorder({
                    encoderPath: '/static/bower_components/opus-recorderjs/dist/waveWorker.min.js',
                    encoderSampleRate: sample_rate // THIS NEEDS TO BE THE SAMPLE RATE OF THE MICROPHONE
                }); 
            
            }

            // Have recorder listen for when the data is available
            recorder.addEventListener("dataAvailable", function(e) {
                audioBlob = new Blob( [e.detail], {type: 'audio/wave'});
                fileName = new Date().toISOString() + ".wav";
                var audioURL = URL.createObjectURL( audioBlob );
                audio.src = audioURL;
                audio.load()
                $('.circle-button-container').find('.play').show()
            });

            recorder.addEventListener("streamReady", function(e) {
                hide_loading();
                recorder.start()
                $('.circle-button-container').find('.record').hide()
                $('.circle-button-container').find('.stop').show()

                setTimeout(function(){
                    visualize2(recorder);
                    },200);
                

            });

            $('.foreground-circle.record').removeClass('unclicked-circle').addClass('clicked-circle');
            
            setTimeout(function(){recorder.initStream();},200);


        }})


    $('#stop-button').click(function(){
        $('.circle-button-container').find('.stop').hide()
        
        $('.circle-button-container').find('.play').show()    
        

        // Stop recorder if active and set recording state to false
        recording = false
        recorder.stop()

        $('.redo').removeClass('disabled');

        $('.foreground-circle.record').removeClass('clicked-circle').addClass('unclicked-circle');

         

            // // $('.circle-text.record').show();
            // // $('.circle-button-container .stop').hide()
            // 
            // $('.circle-button-container .record').hide()
    })

    // WHen sentence is loaded, show the record button
    // $('#play-button').bind('ready', function(){
    //     $('#record-button').show();
    // });    

    // If play button clicked, play audio
    // $('#play-button').click(function(){
    //     audio.play();
    //     $('.foreground-circle.play').removeClass('unclicked-circle').addClass('clicked-circle');
    // });

    // When audio is done playing back, revert button to initial state
    $('#play-audio').bind('ended', function(){        
        $('.redo').removeClass('disabled');
        $('.save').removeClass('disabled');
    });

    $(".redo").click(function(e) {
        if (!$(e.currentTarget).hasClass('disabled')){
            recorder.stop();
            recorder.clearStream();
            audio.pause();
            delete recorder

            $('.foreground-circle.play').addClass('unclicked-circle').removeClass('clicked-circle');
            $('.circle-button-container').find('.play, .stop').hide();
            $('.redo').addClass('disabled');
            $('.save').addClass('disabled');
            $('.circle-button-container .record').show();
        }
    });

    // If "save audio" button clicked, create formdata to save recording model
    $('.save').click(function(e){
        if (!$(e.currentTarget).hasClass('disabled')){
            recorder.stop();
            audio.pause();
            $('.redo').addClass('disabled');
            $('.save').addClass('disabled');
            $('.next').addClass('disabled');
            // Initialize FormData
            var fd = new FormData();
            // Set enctype to multipart; necessary for audio form data
            fd.enctype="multipart/form-data";

            // Add audio blob as blob.wav to form data
            fd.append('audio_file', audioBlob, fileName);

            // Append necessary person and sentence pks to form data to add to recording model
            fd.append('person', person_pk);
            fd.append('sentence', sentences.sentence.id);

            // Send ajax POST request back to corpus/views.py
            console.log(person_pk)
            console.log(sentences.sentence.id)
            console.log(fd)

            show_loading();

            $.ajax({

                type: 'POST',
                url: '/record/',
                data: fd,
                processData: false,
                contentType: false,
                success: function(data) {
                    // Reload the page for a new sentence if recording successfully saved;
                    // Session stores a reload value to display a thank you message 
                    console.log("Recording data successfully submitted and saved");
                    sessionStorage.setItem('reload', "true");
                    
                    // if (window.location.href.search('\\?sentence=')>0){
                    //  window.history.back();
                    // } else {
                    //  window.location.reload();
                    // }
                    // recorder.clearStream();

                    delete audioBlob
                    delete fileName
                    delete audioURL
                    // delete recorder
                    var audioBlob, fileName;

                    $('.circle-button-container .play').hide()
                    $('.circle-button-container .record').show()
                    audio.src = null;
                    hide_loading()
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
    });




}

// visualiser setup - create web audio api context and canvas
// pinched from https://github.com/mdn/web-dictaphone/blob/gh-pages/scripts/app.js
var audioCTX = new (window.AudioContext || webkitAudioContext)();
var canvas = document.querySelector('.visualizer');
var canvacCTX = canvas.getContext("2d");

function visualize2(my_object){

    var src = my_object.sourceNode
    var analyser = my_object.audioContext.createAnalyser();

    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;

    src.connect(analyser);
    // analyser.connect(audioCTX.destination);

    analyser.fftSize = 32;

    var bufferLength = analyser.frequencyBinCount;
    console.log(bufferLength);

    var dataArray = new Uint8Array(bufferLength);
    console.log(dataArray)

    var WIDTH = canvas.clientWidth;
    var HEIGHT = canvas.clientHeight;
    console.log(HEIGHT)

    var barWidth = (WIDTH / bufferLength) ;
    var barHeight;
    var x = 0;

    console.log(barHeight)
    function renderFrame() {
      requestAnimationFrame(renderFrame);

      x = 0;

      analyser.getByteFrequencyData(dataArray);
      // console.log(dataArray)
      canvacCTX.clearRect(0, 0, WIDTH, HEIGHT);
      canvacCTX.fillStyle = "#333";
      canvacCTX.fillRect(0, 0, WIDTH, HEIGHT);

      for (var i = 0; i < bufferLength; i++) {

        barHeight = dataArray[i]*.35;
        
        var h = 345//..barHeight + (25 * (i/bufferLength));
        var s = 73 * ( HEIGHT/barHeight * .5) //250 * (i/bufferLength);
        var l = 10+ 80*( barHeight/HEIGHT )   ;//20;
        

        canvacCTX.fillStyle = "hsl(" + h + "," + s + "%," + l + "%)";
        canvacCTX.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);

        x += barWidth + 1;

        // console.log(parseInt(barHeight), HEIGHT)

        i = bufferLength
      }
    }

    renderFrame();  
}

// navigator.mediaDevices.getUserMedia({audio: true, video: false}).then(
//     function(mediaStream){
//         console.log('Yay')   
//     }
// );



// if (navigator.userAgent.match(/(iPod|iPhone|iPad)/)) {

//     $('.vis-container').remove()

// } else {
//     navigator.mediaDevices.getUserMedia({audio: true, video: false}).then(
//         function(mediaStream){
                // var sourceNode = audioCTX.createMediaStreamSource(mediaStream);
                // my_object = {}
                //my_object['sourceNode'] = sourceNode
//             visualize2(my_object);        
//         });   
// }



