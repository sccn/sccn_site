function [pp_flips, eye_near_flips] = eyetracker_analysis(allStreams, video_brightness)

    bs_no = 1; % biosemi stream (in this case screen brightness
    bs_chann = 1; % 1 and 2 are different -- decide how to deal with this
    bs_adj = .00772;        
    
    pp_mark_no = 2; % psycho physics markers
    pp_adj = -.01613;

    eye_mark_no = 6; % markers from the eye tracking camera
    scene_mark_no = 7; % markers from the scene camera (which does the bulk of the analysis)
    scene_stream_no = 9;    

    bs = allStreams.item{bs_no}.data(:,bs_chann);
    bs_ts = allStreams.item{bs_no}.timeStamp - bs_adj;% - scrn_adj;
    bs_sr = allStreams.item{bs_no}.samplingRate;
    
    pp_ts = allStreams.item{pp_mark_no}.timeStamp - pp_adj;
    pp_vals = allStreams.item{pp_mark_no}.event.label;
    pp_flip = 'flip';
    pp_on = 'white';
    pp_off = 'black';
    
    % we don't need timestamps, because the data are time stamps already
    % channel 1 is open
    % channel 2 is close
    % channel 3 is frame number -- which is not particularly meaningful
    eye_mark = allStreams.item{eye_mark_no}.data;
    scene_mark = allStreams.item{scene_mark_no}.data;
    eye_mark_ts = allStreams.item{eye_mark_no}.timeStamp;
    scene_mark_ts = allStreams.item{scene_mark_no}.timeStamp;
    
    scene_adj = 0.0289;
    scene_stream_ts = allStreams.item{scene_stream_no}.timeStamp - scene_adj;% - .004;
    scene_stream_frames = allStreams.item{scene_stream_no}.data(:,1);

    % find the offset between the timestamp recorded (starting from 0 in mobilab)
    % and the actual timestamp delivered in the streams
    offset = eye_mark(1,2) - eye_mark_ts(1);
    eye_mark(:,1:2) = eye_mark(:,1:2) - offset; 

    offset = scene_mark(1,2) - scene_mark_ts(1);
    scene_mark(:,1:2) = scene_mark(:,1:2) - offset; 

    % interpolate the signals so that they are all on the same timescale
    % align them to the biosemi timestamps
    nan_pad = 1500 % this avoids the NANs that result form interp1

    x = bs_ts;
    xi = bs_ts;
    y = bs;
    yi = interp1(x, y, xi);
    yi = yi';
    bs = yi(1+nan_pad: length(yi)-nan_pad);

    % we can use the frame number that we recorded using our
    % our modification to gaze stream to index the corresponding frames from the
    % video brightnes recording
    vb = zeros(1, length(scene_stream_ts));
    for(n=1:length(vb)-1)
      vb(n) = video_brightness(scene_stream_frames(n)+1);
    end%for
    %scene_stream_ts = scene_stream_ts(1:length(eye_mark_ts));

    x = scene_stream_ts;
    xi = bs_ts;
    y = vb;
    yi = interp1(x, y, xi);
    yi = yi';
    vb1 = yi(1+nan_pad: length(yi)-nan_pad);
% 
%     x = (eye_mark_ts - scene_adj);
%     xi = bs_ts;
%     y = vb;
%     yi = interp1(x, y, xi);
%     yi = yi';
%     vb2 = yi(1+nan_pad: length(yi)-nan_pad);


    % finally, adjust the time stamps to correspond to our truncated data
    bs_ts = bs_ts(1+nan_pad: length(bs_ts)-nan_pad);

    % plot the computation statistics
    if(length(scene_mark_ts)>=length(eye_mark_ts))
      mark_ts = eye_mark_ts;
    else
      mark_ts = scene_mark_ts;
    end%if
    ts_len = length(mark_ts);
    scene_stream_ts = scene_stream_ts(1:ts_len);

    figure;
    hold all;
    plot(mark_ts, scene_mark(1:ts_len,2) - eye_mark(1:ts_len,1),'o');
    plot(mark_ts, eye_mark(1:ts_len,2) - eye_mark(1:ts_len,1),'mo');
    plot(mark_ts, scene_mark(1:ts_len,2) - scene_mark(1:ts_len,1),'go');
    leg = legend('scene end - eye start', 'eye end - eye start', 'scene end - scene start');
    set(leg, 'location', 'northeast');
    xlabel('Time (s)');
    ylabel('Time (s)');
    hold off;

    figure;
    histFig_noK(1000*(scene_stream_ts(1:ts_len)' - eye_mark(1:ts_len,1)+scene_adj), 'Scene Stream Timestamps - Eye Start');

    
    % filter the video signals
    [z,p,k] =  butter(9,20/(bs_sr/2),'low'); % 9th order,  40 hz / (samplingrate/2), low pass
    [sos,g] = zp2sos(z,p,k);
    bs = filtfilt(sos,g,bs);
    vb1 = filtfilt(sos, g, vb1);
   % vb2 = filtfilt(sos, g, vb2);
    
   
    % normalize
    bs_std = std(bs);
    bs = (bs-mean(bs))/bs_std;

    vb1_std = std(vb1);
    vb1 = (vb1-mean(vb1))/vb1_std;

      
    figure;
    plot(bs_ts, bs,'blue');
    hold all;
    plot(bs_ts, vb1+5, 'm');
    %plot(bs_ts, vb2+20, 'black');
    ylim = get(gca, 'YLim');
    leg = legend('BioSemi','Video adjusted to scene camera timestamps');%, 'Video adjusted to eye camera timestamps');
    set(leg, 'location', 'northeast');
    xlabel('Time (s)');
    ylabel('Amplitude / Standard Deviation');
    for(n=1:10000)
      %line([scene_mark(n,1),scene_mark(n,1)], ylim, 'color', 'g');
      %line([scene_mark(n,2),scene_mark(n,2)], ylim, 'color', 'g');
      %line([eye_mark(n,1),eye_mark(n,1)], ylim, 'color', 'g');
      line([scene_stream_ts(n),scene_stream_ts(n)], ylim, 'color', 'g');
    end%for
    

    pp_ons = zeros(size(pp_ts));
    pp_ons_cnt = 1;

    pp_offs = zeros(size(pp_ts));
    pp_offs_cnt = 1;

    pp_flips = zeros(size(pp_ts));
    pp_flips_cnt = 1;


    %find the times of white, black and flip from the PsychoPhysics stream
    for(n=1:length(pp_ts))
      if(strcmp(pp_vals(n), pp_on))
	pp_ons(pp_ons_cnt) = pp_ts(n);
	pp_ons_cnt = pp_ons_cnt + 1;

      end%if

     if(strcmp(strtrim(pp_vals(n,:)), pp_off))
	pp_offs(pp_offs_cnt) = pp_ts(n);
	pp_offs_cnt = pp_offs_cnt + 1;
     end%if

      if(strcmp(pp_vals(n), pp_flip))
	pp_flips(pp_flips_cnt) = pp_ts(n);
	pp_flips_cnt = pp_flips_cnt + 1;
      end%if
    end %for	
    pp_ons = pp_ons(1:pp_ons_cnt-1);
    pp_offs = pp_offs(1:pp_offs_cnt-1);
    %pp_flips = pp_flips(1:2:pp_flips_cnt-1); % remove every other flip to make
    % the sample rates agree 60hz to 30hz

    pp_ons_cnt
    for(n=1:200)
      line([pp_ons(n),pp_ons(n)], ylim, 'color', 'black');
      line([pp_offs(n),pp_offs(n)], ylim, 'color', 'black');
    end%for

    for(n=1:10000)
      line([pp_flips(n),pp_flips(n)], ylim, 'color', 'r');
    end%for


    pre_time = .08;
    on_cnt = 1
    
    scene_flip_diffs = zeros(size(scene_stream_ts));
    % near flip events
    idx = 1;
    for (n=1:length(scene_stream_ts))
      min = Inf;
      
      while (abs(pp_flips(idx) - scene_stream_ts(n))<min&&idx<length(pp_flips))
        min =  abs(pp_flips(idx) - scene_stream_ts(n));
        idx = idx + 1;
      end
      
      scene_flip_diffs(n) = scene_stream_ts(n) - pp_flips(idx-1);
    end
    
    figure;
    histFig_noK(1000*scene_flip_diffs, 'Scene latencies from flip events');
    figure;
    plot(1000*scene_flip_diffs,'o');
    xlabel('examples');
    ylabel('time (ms)');
  
   
   
end%fucntion
