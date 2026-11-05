% This script is written to assess the latency of the 
% eyetracking system (with hotspots) compared to the BioSemi DAQ device
% written by David Medine and Makoto Mayakoshi, SCCN

% %% timeStamp continuity check
% tmp = mobilab.allStreams.item{1}.timeStamp;
% figure; plot(tmp)
% tmp = diff(tmp);
% figure; plot(tmp)
% 
% %% data check
% % figure; plot(detrend(mobilab.allStreams.item{1}.data(1:1000,:), 'constant'));
% % figure; plot(detrend(mobilab.allStreams.item{1}.auxChannel.data(1:1000,:), 'constant'));
% 
% % Here are 8-ch EOG channel signals
% figure; plot(detrend(mobilab.allStreams.item{1}.auxChannel.data(1:1000,2:9), 'constant'));

%% extract EOG channel signals
signal = mobilab.allStreams.item{1}.auxChannel.data(:,2:9);
signal = signal';

%% import data
EEG = pop_importdata('dataformat','array','nbchan',0,'data','signal','srate',512,'pnts',0,'xmin',0);

%% channel location
%EEG = pop_chanedit(EEG, 'load',{'/data/mobi/Digitization_Files/ZebrisData_upto_07_11_2014/David''s_Test/David_121214_Test.sfp' 'filetype' 'autodetect'});
% windows version of the above
EEG = pop_chanedit(EEG, 'load',{'Z:\data\20140502-eyetracker-heatmap\20141202_CES\David_121914_58A_CES_EyetrackerTest.sfp', 'filetype', 'autodetect'});
%% filter
EEG = pop_eegfiltnew(EEG, [], 1, 1690, true, [], 0);

%% re-referencing
EEG = pop_reref( EEG, [1 2] );

%% ica
EEG = pop_runica(EEG, 'extended',1,'interupt','on');

% use VisEd http://sccn.ucsd.edu/wiki/Plugin_list_process to hand-process
% (annotate) the data interactively!

%% the first component is the only one of interest here
EEG = pop_subcomp( EEG, [2  3  4  5  6], 0);

%% for whatever, I didn't get the icaact in my data structure, this fixes it
EEG = eeg_checkset(EEG,'ica');
 
%% get the first component into an array
eeg_em = double(EEG.icaact);
eeg_late = .00772; % conventional BioSemi latency
eeg_em_ts = mobilab.allStreams.item{1}.timeStamp - eeg_late;

%% reject the end, data if data is no good, use visual inspection
% skip if unnecessary
new_end = 150000;
eeg_em = eeg_em(1:new_end);
eeg_em_ts = eeg_em_ts(1:new_end);


%% now get the eyetracking signal
throw_away = 1; % got this with visual inspection
camera_latency = .00289; % measured latency of eyetracker camera
et_lr = mobilab.allStreams.item{4}.data(throw_away:end, 1);
et_lr_ts = mobilab.allStreams.item{4}.timeStamp(throw_away:end) -camera_latency;
%figure; plot(et_lr_ts,et_lr);

%% line up the eeg data to the eyetracker data
n=1;
while(eeg_em_ts(n)<=et_lr_ts(1))
    n=n+1;
end%while
%n
eeg_em = eeg_em(n:end);
eeg_em_ts = eeg_em_ts(n:end);

%% chop off the end of the eyetracking data as well
n=1;
while(et_lr_ts(n)<eeg_em_ts(end))
    n=n+1;
end%while
et_lr = et_lr(1:n);
et_lr_ts = et_lr_ts(1:n);


%% filter and normalize the signals
[z,p,k] =  butter(9,20/(EEG.srate/2),'low'); % 9th order,  40 hz / (samplingrate/2), low pass
[sos,g] = zp2sos(z,p,k);
eeg_em = filtfilt(sos,g,eeg_em);

eegStd = std(eeg_em);
eeg_em = (eeg_em-mean(eeg_em))/eegStd;

% we also need this
eeg_diffs = diff(eeg_em);

figure; plot(eeg_em_ts, eeg_em);
hold;

[z,p,k] =  butter(9,20/(mobilab.allStreams.item{4}.samplingRate/2),'low'); % 9th order,  40 hz / (samplingrate/2), low pass
[sos,g] = zp2sos(z,p,k);
et_lr = filtfilt(sos,g,et_lr);
etStd = std(et_lr);
et_lr = (et_lr-mean(et_lr))/etStd;
plot(et_lr_ts, et_lr+5);



%% find the shifts from one marker to another
% figure; plot(eeg_em_ts(1:end-1), eeg_diffs);
% thresh = .05; % this needs adjustment, plot eeg_diffs for an indication
% 
% eeg_mark = zeros(size(eeg_em));
% ylim = get(gca,'Ylim');
% roi = 400; % this needs to be fine tuned or else below is an infinite loop
% hold off;
% n=1;
% ctr = 1;
% while (n<= length(eeg_diffs))
%     %n
%     if(abs(eeg_diffs(n))> thresh)   
%     % now look for the zero crossing in the region of interest 
%         for(m=1:roi)
%            if(sign(eeg_em(n+m)) ~= sign(eeg_em(n+m+1)))
%                eeg_mark(ctr) = eeg_em_ts(n+m);
%                line([eeg_mark(ctr), eeg_mark(ctr)], ylim, 'color', 'g');
%                ctr = ctr+1;
%                n=n+roi;
%            end%if
%         end%for
%     
%     else
%         n=n+1;  
% 
%     end%if
% end%while
% eeg_mark = eeg_mark(1:ctr-1);

roi = 5;
et_mark = zeros(size(et_lr));
n=1;
ctr = 1;
while (n<= length(et_lr)-1)
    
    if(sign(et_lr(n)) ~= sign(et_lr(n+1)))
        et_mark(ctr) = et_lr_ts(n);
        line([et_mark(ctr), et_mark(ctr)], ylim, 'color', 'r');
        ctr = ctr+1;
        n=n+roi;

    else
        n=n+1;  

    end%if
end%while
et_mark = et_mark(1:ctr-1);

% now that we have these, we look for the same points in the eeg data
eeg_mark = zeros(size(et_mark));
pre_time = .25;
idx = 2;
for (n=1:length(et_mark))
    
    % keep advancing while we are not at the end, and
    % if we are not pre_time before a et marker or if there isn't a zero
    % crossing
    while(idx<length(eeg_em_ts) && eeg_em_ts(idx) < et_mark(n)-pre_time || sign(eeg_em(idx-1)) == sign(eeg_em(idx)))
        idx=idx+1;
        %n
    end%while    
    % these criteria met, make a new marker at that eeg
    % timestamp
    eeg_mark(n) = eeg_em_ts(idx);
    line([eeg_mark(n), eeg_mark(n)], ylim, 'color', 'g');
    
end%for


hold off;

%% histogram the latencies
figure;
histFig_noK(1000*(et_mark-eeg_mark), 'Latency');
scale = linspace(0,eeg_em_ts(end), length(eeg_mark));
figure; plot(scale, 1000*(et_mark-eeg_mark),'x');


%% working on Mobilab data structure
%         
% {
% restoredefaultpath
% rmpath  /data/common/matlab/eeglab
% addpath /data/cta/ozgur/eeglab
% eeglab
% which detectFixationOnsetOffset
% }
% 
% % list stream names
% streamName = cell(length(mobilab.allStreams.item),1);
% for n = 1:length(streamName)
%     streamName{n,1} = mobilab.allStreams.item{n}.name;
% end
% EEG
% % find and import hotspotdata stream
% hotspotdataStreamIdx = find(strcmp(streamName, 'hotspotdata_presenting'));
% 
% % fixationOnsetLatency
% eyeTrackerData = mobilab.allStreams.item{hotspotdataStreamIdx}.data(1:16:end,:); % downsampled to original 30 Hz
% 
% % run Ozgur's first function
% [~,fixationOutput] = detectFixationOnsetOffset(eyeTrackerData,30);
% eyeTrackerLatency  = mobilab.allStreams.item{hotspotdataStreamIdx}.timeStamp(1:16:end); % downsampled to original 30 Hz
% % testing...
% % eyeTrackerLatency = eyeTrackerLatency - eyeTrackerLatency(1,1);
% fixationOnsetLatency  = eyeTrackerLatency(fixationOutput{1,1}); % {1,1} is onset latency
% fixationOffsetLatency = eyeTrackerLatency(fixationOutput{1,2}); % {1,2} is offset latency
% fixationPosition      = fixationOutput{1,3}(:,1:2); % {1,1} is onset latency
% 
% %% import events
% EEG.event    = struct([]);
% EEG.urevent  = struct([]);
% eventCounter = 0;
% 
% for eventTypeIdx = 1:2
%     if     eventTypeIdx == 1; tmpEventName = 'fixOn';  tmpLatencyList = fixationOnsetLatency;
%     elseif eventTypeIdx == 2; tmpEventName = 'fixOff'; tmpLatencyList = fixationOffsetLatency;
%     end
%     
%     for latencyListIdx = 1:length(tmpLatencyList)
%         eventCounter = eventCounter+1;
%         EEG.event(1,eventCounter).type    = tmpEventName;
%         EEG.event(1,eventCounter).latency = binary_findClosest(EEG.times,tmpLatencyList(latencyListIdx)*1000);
%         
%         if eventTypeIdx == 1 % fixation on
%             EEG.event(1,eventCounter).gazeX = round(fixationPosition(latencyListIdx,1)*1600);
%             EEG.event(1,eventCounter).gazeY = round(fixationPosition(latencyListIdx,2)*1200);
%         else
%             EEG.event(1,eventCounter).gazeX = 0;
%             EEG.event(1,eventCounter).gazeY = 0;
%         end
%     end
% end
% 
% eventLatencies = cell2mat({EEG.event.latency}');
% [~,eventSortIdx] = sort(eventLatencies);
% EEG.event = EEG.event(1,eventSortIdx);
% EEG = eeg_checkset(EEG,'makeur');
% eeglab redraw