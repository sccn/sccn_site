function [ frame_brightness ] = processVideoFlashes(movieFile )
%Extractes color changes from a video stream. After the window appears,
%select the region of interest. frame_brightness gives the brightness of
%of each frame of the movie at that location.

    v = mmread(movieFile,1);
    figure('Name', 'Select region of interest:', 'NumberTitle', 'off');
   
    image(v.frames(1).cdata);
    rect = getrect;
    xmin = round(rect(1));
    xmax = xmin+round(rect(3));
    ymin = round(rect(2));
    ymax = ymin + round(rect(3));
    
    if xmin < 1 
        xmin = 1;
    end
    if xmax < 1
        xmax = 1;
    end
    if ymin < 1
        ymin = 1;
    end
    if ymax < 1;
        ymax = 1;
    end
    if xmin > v.width
        xmin = v.width;
    end
    if xmax > v.width
        xmax = v.width;
    end
    if ymin > v.height
        ymin = v.height;
    end
    if ymax > v.height
        ymax = v.height;
    end
    if v.nrFramesTotal > 0
        vlast = mmread(movieFile,v.nrFramesTotal);
    else
        % estimated last frame, try reading past the end of the video, after which nrFramesTotal will be accurate.
        vlast = mmread(movieFile,-v.nrFramesTotal*1.01);
        vlast = mmread(movieFile,v.nrFramesTotal); 
    end
    nFrames = vlast.nrFramesTotal;
    
    
    frame_times=zeros([1,nFrames]);
    frame_brightness=zeros([1,nFrames]);
    % Read one frame at a time.
    BlockSize = 300;
    FrameNum = 1;
    FramesLeft = nFrames;
    while FramesLeft > 0
    %for BlockNum = 1 : ceil(nFrames/BlockSize)
        % disp(['On Frame #',num2str(FrameNum), ' of ',num2str(nFrames)]);
        if FramesLeft > BlockSize        
            ThisBlockSize = BlockSize;
        else        
            ThisBlockSize = FramesLeft;
        end
        v = mmread(movieFile,FrameNum:FrameNum+ThisBlockSize-1);
        for CurFrameIndex = 1 : ThisBlockSize
          
            frame_times(FrameNum) = v.times(CurFrameIndex);
            frame_brightness(FrameNum) = mean2(v.frames(CurFrameIndex).cdata(ymin:ymax,xmin:xmax,1:3));
           % frame_brightness(FrameNum) = mean2(v.frames(CurFrameIndex).cdata(250:480,190:300,1:3));
           %frame_brightness(FrameNum) = mean2(v.frames(CurFrameIndex).cdata(200:250,290:400,1:3));
           
            if (mod(FrameNum,300)==0)
                %progress report every 300 frames
                disp(['On Frame #',num2str(FrameNum), ' of ',num2str(nFrames)]);
            end
            FrameNum = FrameNum+1;
            FramesLeft = FramesLeft-1;
        end  
    end


end

