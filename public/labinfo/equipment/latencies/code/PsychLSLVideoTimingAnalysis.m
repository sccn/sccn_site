
function videoFrames = TESTPsychLSLVideoTimingAnalysis(allDataStreams, frame_brightness)
%Analysis function to test synchrony between LSL events and screen flash
%events. Assumes that there is a video stream, and an EEG stream.
%Written by Matthew Grivich SCCN/UCSD.

    if nargin < 3
        linearize_frames = true;
    end

    
    %These parameters will need to be changed to match the data.
    eegStreamNumber = 1;
    eegChannelNumber = 1;
    stdThreshold = 0.0;
    markerStreamNumber = 2;
    onEvent = 'white';
    offEvent = 'black';
    
    engineStreamNumber = 2;
    engineEvent = 'flip';
    
    videoStreamNumber = 9;
    videoChannelNumber = 1;
    preTime = .10;
    
    eeg =  allDataStreams.item{eegStreamNumber}.data(:,eegChannelNumber); 
    eegTime = allDataStreams.item{eegStreamNumber}.timeStamp;
    eventLatencies = allDataStreams.item{markerStreamNumber}.timeStamp;
    eventVals = char(allDataStreams.item{markerStreamNumber}.event.label);
    eventLatencies = eventLatencies(1:end-1);
    
    engineLatencies = allDataStreams.item{engineStreamNumber}.timeStamp;
    engineVals = char(allDataStreams.item{engineStreamNumber}.event.label);
   
    videoFrames = allDataStreams.item{videoStreamNumber}.data(:,videoChannelNumber);
    videoTime = allDataStreams.item{videoStreamNumber}.timeStamp;

    %this will only not crash if video recording started before and ended
    %after data recording.
    video = zeros(1,length(videoFrames));
    for n=1:length(videoFrames)-1
        video(n) = frame_brightness(videoFrames(n)+1); %for matlab indexing from 1
    end
    
       %find closest engine event to each (already linearized) event.
    engineIndex = 1;
    for eventIndex=1:length(eventLatencies)
        min = Inf;
       
        while (abs(eventLatencies(eventIndex) - engineLatencies(engineIndex)) < min) 
            min =  abs(eventLatencies(eventIndex) - engineLatencies(engineIndex));
            engineIndex = engineIndex +1;
        end
        
        eventLatencies(eventIndex) = engineLatencies(engineIndex-1);
    end
    
    
    samplingRate = allDataStreams.item{eegStreamNumber}.samplingRate;
    
    %filter out high frequency oscillations common in monitor light levels
    [z,p,k] =  butter(9,40/(samplingRate/2),'low'); % 9th order,  40 hz / (samplingrate/2), low pass

    [sos,g] = zp2sos(z,p,k);
    eeg = filtfilt(sos,g,eeg);
 
    onTimes = zeros(1, length(eventLatencies));
    offTimes = zeros(1, length(eventLatencies));
    onCount = 0;
    offCount = 0;
    

    for i=1:length(eventLatencies)
         if strcmp(strtrim(eventVals(i,:)),onEvent)
            onCount = onCount+1;
            onTimes(onCount) = eventLatencies(i);

         end       
       

         if strcmp(strtrim(eventVals(i,:)),offEvent)
            offCount = offCount+1;
            offTimes(offCount) = eventLatencies(i);

         end
    end    
    
    onTimes = onTimes(1:onCount);

    eegStd = std(eeg);
    eeg = (eeg-mean(eeg))/eegStd;
    videoStd = std(video);
    video = (video - mean(video))/videoStd;
    
    figure;
    hold all;
    plot(videoTime, video, 'color', 'black');
    plot(eegTime, eeg + 10, 'color', 'blue');

    leg = legend('Video', 'EEG');
    %leg = legend('Video');
    set(leg,'Location', 'NorthEast');
    set(leg,'Interpreter', 'None');
    
    xlabel('Time (s)');
    ylabel('Volts');
    ylabel('Amplitude / Standard Deviation');
    
    eegIndex = 1;
    videoIndex = 1;
   engineCount = 0;
   ylim = get(gca,'Ylim');
    for i=1:1000 %length(engineLatencies)
        if strcmp(engineVals(i,:),engineEvent)
            engineCount = engineCount+1;
            line([engineLatencies(i),engineLatencies(i)], ylim, 'color','g')
        end
    end    

    onCount = 0;
    
    onLatencies = zeros(1,length(onTimes));
    videoLatencies = zeros(1,length(onTimes));
    
  
    
    %for each event, find screen latency (difference between event marker
    %and onset of light transition)
    for i=1:length(onTimes) 
       
            line([onTimes(i),onTimes(i)], ylim, 'color','r')
 
            while eegIndex < length(eeg) && (eegTime(eegIndex) < onTimes(i) - preTime || eeg(eegIndex) < stdThreshold) 
               
                eegIndex = eegIndex + 1;
            end
          %  onLatencies(i) = eegTime(eegIndex) - onTimes(i);
            %interpolate 
            onLatencies(i) = eegTime(eegIndex-1) + (eegTime(eegIndex) - eegTime(eegIndex-1)) * (stdThreshold - eeg(eegIndex-1)) / (eeg(eegIndex)-eeg(eegIndex-1)) - onTimes(i);
   
             
            while videoIndex < length(video) && (videoTime(videoIndex) < onTimes(i) - preTime || video(videoIndex) < stdThreshold) 
               
                videoIndex = videoIndex + 1;
            end
           % videoLatencies(i) = videoTime(videoIndex) - onTimes(i);
            %interpolate 
            videoLatencies(i) = videoTime(videoIndex-1) + (videoTime(videoIndex) - videoTime(videoIndex-1)) * (stdThreshold - video(videoIndex-1)) / (video(videoIndex)-video(videoIndex-1)) - onTimes(i);
   
             onCount = onCount+1;             
        
    end
%uncomment if you want to look at off times (not analyzed)
%      for i=1:length(offTimes) 
%        
%             line([offTimes(i),offTimes(i)], ylim, 'color','r')
%
%     end
    line(get(gca,'Xlim'),[stdThreshold,stdThreshold],'color','red');
    line(get(gca,'Xlim'),10+[stdThreshold,stdThreshold],'color','red');
    hold off
   

    histFig( onLatencies*1000, 'EEG Latency (ms)' );

    histFig(videoLatencies*1000, 'Video Latency (ms)');
    
    figure
    plot(onTimes,1000*(onLatencies));
    ylabel('EEG delay (ms)');
    xlabel('Event time (s)');
    
    figure
    plot(onTimes,1000*(videoLatencies));
    ylabel('Video delay (ms)');
    xlabel('Event time (s)');
    
    figure
    hold all
    scatter(onLatencies, videoLatencies);
    xlabel('EEG Latency (s)');
    ylabel('Video Latency (s)');
    hold off
    
end

