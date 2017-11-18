


class Visualize{

  constructor(canvas_id, sourceNode, audioContext){
    var self = this
    this.canvas = document.getElementById(canvas_id)
    this.canvasContext = canvas.getContext("2d")
    this.loop = false
    this.sourceNode = sourceNode
    this.audioContext = audioContext
    this.analyser = audioContext.createAnalyser();
    this.analyser.fftSize = 32;


    this.sourceNode.connect(this.analyser);
    
    this.bufferLength = this.analyser.frequencyBinCount;
    this.dataArray = new Uint8Array(this.bufferLength);



  }

  stop(){
    this.loop = false
  }

  start(){
    this.canvas.width = this.canvas.clientWidth;
    this.canvas.height = this.canvas.clientHeight;    
    this.WIDTH = this.canvas.clientWidth;
    this.HEIGHT = this.canvas.clientHeight;    
    this.loop = true
    this.renderFrame();
  }

  renderFrame() {
    var self = this
    if (self.loop){
      window.requestAnimationFrame(function(){self.renderFrame()});
      self.analyser.getByteFrequencyData(self.dataArray);
      self.canvasContext.clearRect(0, 0, self.WIDTH, self.HEIGHT);
      self.canvasContext.fillStyle = "#333";
      self.canvasContext.fillRect(0, 0, self.WIDTH, self.HEIGHT);

      var barWidth = (self.WIDTH / self.bufferLength)
      var barHeight = 0
      var x = 0;

//       console.log(

//         self.dataArray.reduce(function(a, b) {
//     return Math.max(a, b);
// })

        // )

      for (var i = 0; i < self.bufferLength; i++) {
        barHeight = self.dataArray[i]/255*self.HEIGHT*.9;
        
        var h = 345
        var s = 73 * ( self.HEIGHT/barHeight * .5) 
        var l = 90 * ( barHeight/self.HEIGHT)
        
        self.canvasContext.fillStyle = "hsl(" + h + "," + s + "%," + l + "%)";
        self.canvasContext.fillRect(x, self.HEIGHT - barHeight, barWidth, barHeight);

        x += barWidth + 1;

        // console.log(parseInt(barHeight), self.HEIGHT)

      }
    } else {
      return;
    }
  }

}
