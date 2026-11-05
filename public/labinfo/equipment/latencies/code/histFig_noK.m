function [ output_args ] = histFig( data, dataLabel, spr, spc, spn )
   %figure
   if(nargin>2)
       subplot(spr, spc, spn)
   end%if
   hist(data,20, '5');
   xlabel(dataLabel);
   ylabel('Samples');
   h = findobj(gca,'Type','patch');
   
%    ticks = get(gca, 'ytick');
%    ticks = ticks/1000;1
%    ticklabels = cell(size(ticks));
%    
%    for(m=1:length(ticks))
%       ticklabels{m} = sprintf('%dk\n',ticks(m));
%    end%for
    
%   set(gca, 'yticklabel', ticklabels);
   
   maxCount = get(gca,'Ylim');
   ylim([maxCount(1) maxCount(2)+50]);
   %ylim([3 10]);
   q = quantile(data, [.05 .5 .95]);
   median = q(2);
   centile5 = q(1);
   centile95 = q(3);
   meanVal = mean(data);
   rms = std(data);
   maxCount = maxCount(2)-2;
   
   %text(min(data),maxCount, sprintf('mean = %.5f ms\nrms = %.5f ms\nmedian = %.5f ms\n5th centile = %.5f ms\n95th centile = %.5f ms\n',  meanVal,rms,median,centile5, centile95), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'top');
   leg = text(min(data),maxCount, sprintf('5th centile = %.3f ms\nmean = %.3f ms\nmedian = %.3f\n95th centile = %.3f ms\n',  centile5, meanVal,median, centile95), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'top');
   %'HorizontalAlignment', 'left', 'VerticalAlignment', 'top'
    set(leg);% 'FontSize',14);    
    %xax = get(gca, 'xlabel');
    %set(xax, 'FontSize', 14);

end

