function [foo]= phasespace_latency_analysis2(allStreams, invert_ps, range, ps_shift, bs_shift)

% code to analyze phasespace vs biosemi data acquistion lag
% args:
%      allStreams -- the mobilab data streams giving the biosemi and
%          phasespace data etc.
%      invert_ps -- (optional) flag to indicate whehter or not to invert the polarity
%          of the phasespace signal 
%          default is 1 (invert)
%      range -- (optional) range of data in the streams to analyze -- cross
%          correlated the 'stationary part of the streams does no good as it is
%          literally just noise
%      ps_shift -- (optional) amount to shifr the phasespace stream
%          + values shift left, - values shift right 
%      bs_shift -- (optional) amount to shift the biosemi stream

% written by David Medine -- SCCN/UCSD

foo = 1; %fake return argument

    if nargin<2
        invert = 1;
    else invert = invert_ps;        
    end%if
    
    if nargin<4 
          ps_shift = 0;
    else
        ps_shift = -1 *ps_shift;
    end%if
    
    if nargin<5 
          bs_shift = 0;
          
    else
        bs_shift = -1 *bs_shift;
    end%if

    bs_stream_num = 1; %biosemi stream id
    bs_data_num = 1; %bio semi stream data id
    ps_stream_num = 2; %ps stream id
    ps_dataX_num = 49; %
    ps_dataY_num = 50; %
    ps_dataZ_num = 51; %
    % these indices may need to be adjusted depending on the setup
    
    
    it1 = allStreams.item{bs_stream_num};
    it2 = allStreams.item{ps_stream_num};  
    
    %data
    bs_data = it1.data(:,bs_data_num);
    ps_dataX = it2.data(:,ps_dataX_num);
    ps_dataY = it2.data(:,ps_dataY_num);
    ps_dataZ = it2.data(:,ps_dataZ_num);
    ps_data = sqrt(ps_dataX.*ps_dataX + ps_dataY.*ps_dataY +ps_dataZ.*ps_dataZ);
    %size(bs_data)
    
    %sampling rates
    bs_sr = it1.samplingRate;
    ps_sr = it2.samplingRate;
    
        %prep the signals
    if(invert==1)
        ps_data = ps_data .*-1;
    end%if
    
        %filter out high frequency oscillations common in monitor light levels
    [z,p,k] =  butter(9,20/(ps_sr/2),'low'); 
    [sos,g] = zp2sos(z,p,k);
    ps_data = filtfilt(sos,g,ps_data);
    ps_data = ps_data-mean(ps_data);
    ps_data = ps_data/std(ps_data);
  
    
       %filter out high frequency oscillations common in monitor light levels
    [z,p,k] =  butter(9,20/(bs_sr/2),'low'); % 9th order,  40 hz / (samplingrate/2), low pass

    [sos,g] = zp2sos(z,p,k);
    bs_data = filtfilt(sos,g,bs_data);
    bs_data = bs_data-mean(bs_data);
    bs_data = bs_data/std(bs_data);
    
    
    %timestamps
    bs_ts = it1.timeStamp;
    ps_ts = it2.timeStamp;
    %size(bs_ts)
    
    %sampling rates
    bs_sr = it1.samplingRate;
    ps_sr = it2.samplingRate;
    
    if(nargin<3)
        range = [1,length(bs_data)]
    end%if
    
    %stretch the ps stream to align with biosemi timestamps 
    %rather than data collection indeces
    x = ps_ts + (ps_shift * .001);
    xi = bs_ts;
    y = ps_data;
    yi = interp1(x,y,xi);
    yi = yi';
    
    nan_pad =  200;% add this to avoid the NaNs that result in the first few dozen slots after interp1
    ps_adj = yi(range(1)+nan_pad:range(2));

    %align biosemi with its own timestamps
    x = bs_ts + (bs_shift * .001);
    xi = bs_ts;
    y = bs_data;
    yi = interp1(x,y,xi);
    yi = yi';

    bs_adj = yi(range(1)+nan_pad:range(2));
    bs_ts_adj = bs_ts(range(1)+nan_pad:range(2)) + bs_shift;

    %cross correlate    
    psCCbs = xcorr(ps_adj, bs_adj);%, bs_sr, 'unbiased');
    bsCCbs = xcorr(bs_adj, bs_adj);%, bs_sr, 'unbiased');
    
    %find the peaks
    [mx, idx] = max(psCCbs);
    psCCbs_max = [mx, idx];
    [mx, idx] = max(bsCCbs);   
    bsCCbs_max = [mx, idx];
    
    latency_samps = -1*(bsCCbs_max(2) - psCCbs_max(2));
    latency_ms = 1000 * latency_samps/bs_sr
    
    
     sz_ps_adj = size(ps_adj);

    figure;
    plot(psCCbs,'x');
    ylim = get(gca,'Ylim'); 
    hold on;
    line([sz_ps_adj(1),sz_ps_adj(1)], ylim, 'color', 'g');
    line([psCCbs_max(2),psCCbs_max(2)], ylim, 'color', 'r');  
    leg = text(100, ylim(2) - .2*ylim(2), sprintf(' latency ms = %.5f\n latency samples %d', latency_ms, latency_samps));
    hold off;    

    %break the data into windows for more detailed cross correlation
    win_cnt = 10;
    new_range = length(ps_adj);
    win_sz = floor(new_range/win_cnt);%10000;
    win_times = zeros(1, win_cnt);

    ps_temp = zeros(win_sz, win_cnt);
    bs_temp = ps_temp;
    
    ps_tempCCbs_temp = zeros(win_sz *2 -1, win_cnt);
    bs_tempCCbs_temp = ps_tempCCbs_temp;    
    
    for(n=1:win_cnt)
         n
        win_times(n) = (.5*n) * (range(2) - range(1))/win_cnt;
        ps_temp(:,n) = ps_adj((n-1)*win_sz + 1:n*win_sz);
        bs_temp(:,n) = bs_adj((n-1)*win_sz + 1:n*win_sz);
        ps_tempCCbs_temp(:,n) = xcorr(ps_temp(:,n), bs_temp(:,n));%, bs_sr, 'unbiased');
        bs_tempCCbs_temp(:,n) = xcorr(bs_temp(:,n), bs_temp(:,n));%, bs_sr, 'unbiased');
    end%for
        

    idxs_ps = zeros(1, win_cnt);
    idxs_bs = zeros(1, win_cnt);    
    
    for(k=1:win_cnt)
        [mx, idxs_ps(k)] = max(ps_tempCCbs_temp(:,k));
        [mx, idxs_bs(k)] = max(bs_tempCCbs_temp(:,k));
    end%for

    latencies = -1000*((idxs_bs - idxs_ps)/bs_sr);

    mn_mdn = zeros(length(idxs_ps), 2);    
    mn_mdn(:,1) = mn_mdn(:,1) + mean(latencies);
    mn_mdn(:,2) = mn_mdn(:,2) + median(latencies);
    mn = mean(latencies)   
    err = std(latencies)/sqrt(win_cnt)
    
    figure
    plot(win_times, latencies);  
    hold on
    %plot(mn_mdn);
   % plot(mn_mdn(:,1),'r');
    %plot(mn_mdn(:,2),'g');
    %leg = legend('Latencies', 'Mean', 'Median');
    %set(leg, 'Location', 'NorthEast');
    xlabel('Time (s)');
    ylabel('Overall Lag (ms)');
    hold off;


    

end%function