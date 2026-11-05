function [latencies] = controller_analysis( allStreams )
%clear;
foo = 0;
    bs_num   = 1; % 
    bttn_num = 2; % 
    
    bs_lag = -.00772; % measured already
    
    bs_sr = allStreams.item{bs_num}.samplingRate;
    
    bs_chann = 1;
    
    bs = allStreams.item{bs_num}.data(:,bs_chann) *-.001; % convert millivolts to volts and invert
           
    
     % filter out high frequency -- this may be wholly unnecessary
     [z,p,k] =  butter(9,20/(bs_sr/2),'low'); 
     [sos,g] = zp2sos(z,p,k);
     bs = filtfilt(sos,g,bs);
     bs = bs-mean(bs);
     bs = bs/std(bs);
     bs = bs/max(bs);
    
     bs_ts = allStreams.item{bs_num}.timeStamp + bs_lag; 
%     bs_diff = zeros(size(bs));
%     for(n=1:length(bs)-1)
%         bs_diff(n)  = bs(n+1) - bs(n);
%     end%for
%     bs = bs_diff;
    
    bttn    = allStreams.item{bttn_num}.event.label;
    bttn_ts = allStreams.item{bttn_num}.timeStamp;
%size(bttn_ts)   
    bttn_dn = 'Button2 pressed';
    bttn_up = 'Button2 released';

    
     dn_cnt = 0;
     up_cnt = 0;      

     
    post_time = .1;% *bs_sr; % 
    pre_time = .05;% *bs_sr; % 
    
    latencies = zeros(dn_cnt,4);
    true_cnt = 1;
     



    figure;
    hold all;
    plot(bs_ts, bs, 'color', 'black');
   
    %leg = legend('PhaseSpace Magnitude');
    %leg = legend('Video');
    %set(leg,'Location', 'NorthEast');
    %set(leg,'Interpreter', 'None');
    
    %xlabel('Time (s)');
    
    %ylabel('Amplitude / Standard Deviation');
    
    
    ylim = get(gca,'Ylim');
    dn_ts = zeros(size(bttn_ts));
    up_ts = zeros(size(bttn_ts));
    for n=1:length(bttn_ts)
        if(strcmp(bttn(n,:),bttn_dn))
            dn_cnt = dn_cnt+1;
            dn_ts(dn_cnt) = bttn_ts(n);
            line([bttn_ts(n),bttn_ts(n)], ylim, 'color','g')
        end%if
         if(strcmp(bttn(n,:),bttn_up))
             up_cnt = up_cnt+1;
             up_ts(dn_cnt) = bttn_ts(n);  
             line([bttn_ts(n),bttn_ts(n)], ylim, 'color','r')
         end%if        
    end%for

    dn_ts = dn_ts(1:dn_cnt);
    up_ts = up_ts(1:dn_cnt);
    %find local minima relative to button down events
    dn_stats = zeros(dn_cnt, 6); %[min_val, min_idx, min_ts, max_val, max_idx, max_ts]
    for(n=1:dn_cnt)
        
        open = floor((dn_ts(n) - post_time)* bs_sr);
        close = floor((dn_ts(n) + pre_time)* bs_sr);
        win = bs(open:close);
        [max_val, max_idx] = max(win);
        [min_val, min_idx] = min(win);
        dn_stats(n,:) = [min_val, open+min_idx-1, bs_ts(open+min_idx-1), max_val, open + max_idx-1, bs_ts(open + max_idx-1)]; 
    end%for
        
    for(n=1:up_cnt)
        
        open = floor((up_ts(n) - post_time)* bs_sr);
        close = floor((up_ts(n) + pre_time)* bs_sr);
        win = bs(open:close);
        [max_val, max_idx] = max(win);
        [min_val, min_idx] = min(win);
        up_stats(n,:) = [min_val, open+min_idx-1, bs_ts(open+min_idx-1), max_val, open + max_idx-1, bs_ts(open + max_idx-1)]; 
    end%for
    
    plot(dn_stats(:,6), dn_stats(:,4), 'x');
    plot(up_stats(:,3), up_stats(:,1), 'x');
        
    hold off;   

    size(dn_ts);
    size(dn_stats);
    dn_late = dn_ts' - dn_stats(:,6);
  

    figure
    histFig( dn_late*1000, 'Button Down Latency (ms)' );
%     
    up_late = up_ts' - up_stats(:,3);

    figure
    histFig( up_late*1000, 'Button Up Latency (ms)' );

    
end%function

