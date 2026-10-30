class MarVoiPCM extends AudioWorkletProcessor {
  constructor(){super();this.chunk=new Float32Array(320);this.at=0;}
  process(inputs,outputs){
    const data=inputs[0]?.[0];
    if(data)for(let i=0;i<data.length;i++){
      this.chunk[this.at++]=data[i];
      if(this.at===this.chunk.length){const out=this.chunk;this.port.postMessage({samples:out,rate:sampleRate},[out.buffer]);this.chunk=new Float32Array(320);this.at=0;}
    }
    return true;
  }
}
registerProcessor('marvoi-pcm',MarVoiPCM);
