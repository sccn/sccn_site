function [latencies] = click_analysis( allStreams )
%clear;
    ps_num   = 2; % from phase space
    clck_num = 1; % from ClickMe
    
    ps_lag = .0056; % measured already
    
    ps_sr = allStreams.item{ps_num}.samplingRate;
    
    psX_num = 10;   
    psY_num = psX_num+1;
    psZ_num = psX_num+2;
    
    psX = allStreams.item{ps_num}.data(:,psX_num); % X
    psY = allStreams.item{ps_num}.data(:,psY_num); % Y
    psZ = allStreams.item{ps_num}.data(:,psZ_num); % Z
       
    % magnitude of the motion (no direction)
    ps_mags = sqrt(psX .* psX + psY .* psY + psZ .* psZ);
    
    % filter out high frequency -- this may be wholly unnecessary
%     [z,p,k] =  butter(9,20/(ps_sr/2),'low'); 
%     [sos,g] = zp2sos(z,p,k);
%     ps_mags = filtfilt(sos,g,ps_mags);
%     ps_mags = ps_mags-mean(ps_mags);
%     ps_mags = ps_mags/std(ps_mags);
    
    ps_ts = allStreams.item{ps_num}.timeStamp - ps_lag;  
    
    clck    = allStreams.item{clck_num}.event.label;
    clck_ts = allStreams.item{clck_num}.timeStamp;

    clck_event = 'Click';
    clck_cnt = length(clck);
    
    post_time = .3 *ps_sr; % back up 300ms worth to find local max
       
    latencies = zeros(clck_cnt,3);
    true_cnt = 1;
    
    for(n=1:clck_cnt)
        if(clck_ts(n)~=0)
            % chunk of ps signal to analyze
            strt = floor(clck_ts(n)*ps_sr - post_time); %start of signal chunck to look at
            stop = floor(clck_ts(n)*ps_sr); %end of signal chunk to look at
            win = ps_mags(strt:stop);
        
          % local min and max
            [win_mxa, win_mxb] = max(win);
            win_min = min(win);
        
           if(win_min ~= 0) % if there is a zero here, it is bad data, so ignore it
     
                latencies(true_cnt,1) = clck_ts(n);
                latencies(true_cnt,2) = ps_ts(win_mxb+strt-1);
                true_cnt = true_cnt+1;
            end%if
        end%if
    end%for

    latencies = latencies(1:true_cnt-1,:);
    latencies(:,3) = latencies(:,1) - latencies(:,2);
    
        figure;
    hold all;
    plot(ps_ts, ps_mags, 'color', 'black');
   
    leg = legend('PhaseSpace Magnitude');
    %leg = legend('Video');
    set(leg,'Location', 'NorthEast');
    set(leg,'Interpreter', 'None');
    
    xlabel('Time (s)');
    ylabel('Amplitude');
    
    cnt = 0;
    ylim = get(gca,'Ylim');
    for n=1:length(clck_ts)
        line([clck_ts(n),clck_ts(n)], ylim, 'color','g')
    end%for
    for n=1:length(latencies(:,2))
        line([latencies(n,2),latencies(n,2)], ylim, 'color','r')
    end%for

    hold off;   
    
    figure
    hold all
    plot(latencies(:,2),latencies(:,3)*1000, 'x');
    xlabel('Time (s)');
    ylabel('Latency (ms)');
    hold off
            
    figure
    histFig_noK( latencies(:,3)*1000, 'Click Latency (ms)' );
    std(latencies(:,3))
    std_err = std(latencies(:,3))/sqrt(length(latencies(:,3)))
end%function

