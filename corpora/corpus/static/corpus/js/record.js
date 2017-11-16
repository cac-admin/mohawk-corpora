var audio = document.getElementById('play-audio');
var recorder
var audioBlob, fileName;

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
                $('#play-button').show();
            });

            recorder.addEventListener("streamReady", function(e) {
                recorder.start()
                $('.circle-button-container .record').hide()
                $('.circle-button-container .stop').show()              
            });

            $('.foreground-circle.record').removeClass('unclicked-circle').addClass('clicked-circle');

            recorder.initStream()

            // setTimeout(function(){},200);


        }})


    $('#stop-button').click(function(){


            // Stop recorder if active and set recording state to false
            recording = false
            recorder.stop()
            
            $('.foreground-circle.record').removeClass('clicked-circle').addClass('unclicked-circle');
            // $('.circle-text.record').show();
            // $('.circle-button-container .stop').hide()
            $('.redo').removeClass('disabled');
            $('.circle-button-container .record').hide()
    })

    // WHen sentence is loaded, show the record button
    // $('#play-button').bind('ready', function(){
    //     $('#record-button').show();
    // });    

    // If play button clicked, play audio
    $('#play-button').click(function(){
        audio.play();
        $('.foreground-circle.play').removeClass('unclicked-circle').addClass('clicked-circle');
    });

    // When audio is done playing back, revert button to initial state
    $('#play-audio').bind('ended', function(){
        $('.foreground-circle.play').removeClass('clicked-circle').addClass('unclicked-circle');
        
        $('.redo').removeClass('disabled');
        $('.save').removeClass('disabled');
    });

    $(".redo").click(function() {
        recorder.stop();
        recorder.clearStream();
        audio.pause();

        $('.circle-button-container').find('.play, .stop').hide();
        $('.redo').addClass('disabled');
        $('.save').addClass('disabled');
        $('.circle-button-container .record').show();
    });

    // If "save audio" button clicked, create formdata to save recording model
    $('.save').click(function(){
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
                sentences.next()

            },
            error: function(xhr, ajaxOptions, thrownError) {
                // Display an error message if views return saving error
                $("#status-message h2").text("Sorry, there was an error!");
                $("#status-message").show();
            }
        });

    });




}

// visualiser setup - create web audio api context and canvas
// pinched from https://github.com/mdn/web-dictaphone/blob/gh-pages/scripts/app.js
var audioCTX = new (window.AudioContext || webkitAudioContext)();
var canvas = document.querySelector('.visualizer');
var canvacCTX = canvas.getContext("2d");

function visualize2(stream){

    var src = audioCTX.createMediaStreamSource(stream);
    var analyser = audioCTX.createAnalyser();

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    src.connect(analyser);
    // analyser.connect(audioCTX.destination);

    analyser.fftSize = 32*4;

    var bufferLength = analyser.frequencyBinCount;
    console.log(bufferLength);

    var dataArray = new Uint8Array(bufferLength);
    console.log(dataArray)

    var WIDTH = canvas.width;
    var HEIGHT = canvas.height;

    var barWidth = (WIDTH / bufferLength) * 2.5;
    var barHeight;
    var x = 0;

    console.log(barHeight)
    function renderFrame() {
      requestAnimationFrame(renderFrame);

      x = 0;

      analyser.getByteFrequencyData(dataArray);
      // console.log(dataArray)
      canvacCTX.clearRect(0, 0, WIDTH, HEIGHT);
      canvacCTX.fillStyle = "rgba(0,0,0,.5)";
      canvacCTX.fillRect(0, 0, WIDTH, HEIGHT);

      for (var i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i]*2;
        
        var r = barHeight + (25 * (i/bufferLength));
        var g = 250 * (i/bufferLength);
        var b = 50;

        canvacCTX.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
        canvacCTX.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);

        x += barWidth + 1;
      }
    }

    renderFrame();  
}

// navigator.mediaDevices.getUserMedia({audio: true, video: false}).then(
//     function(mediaStream){
//         console.log('Yay')   
//     }
// );



if (navigator.userAgent.match(/(iPod|iPhone|iPad)/)) {

    $('.vis-container').remove()

} else {
    navigator.mediaDevices.getUserMedia({audio: true, video: false}).then(
        function(mediaStream){
            visualize2(mediaStream);        
        });   
}



