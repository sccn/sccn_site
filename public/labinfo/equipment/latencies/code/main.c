/**************************************************************/
/* C program to evaluate timings internal and external to LSL */
/* This program sets up lsl outlets to record the time of     */ 
/* 1) Trigerring a voltage spike rise on NIdaq device         */
/* 2) When that spike re-arrives via feedback on NIdaq        */
/* 3) When that same spike re_arrives via biosemi device      */
/*                                                            */
/*             by David Medine, SCCN                          */
/**************************************************************/

#include "NIDAQmx.h"
#include "stdio.h"
#include "stdlib.h"
#include "lsl_c.h"
#include "Windows.h"
#include "stdio.h"

// recommeded by ni website
#define DAQmxErrChk(functionCall) if( DAQmxFailed(NIerr=(functionCall)) ) goto Error; else

#define NISR 10000
// NIdaq sampling rate -- user controlled
#define BSSR 2048
// biosemi sampling rate -- always 2048

//---------------------
//---------------------

int main(void){

	// NIdaq
	int32      NIerr = 0;
	int32      ctr;
	TaskHandle NIth_i; // read (input) task
	TaskHandle NIth_o; // write (output) task
	float64    NIdata_i; // read one sample at a time
	float64    NIdata_o; // write one sample at a time
	float    nidaq_send_data; // type casting
	float    nidaq_receive_data;
	double ts;
	char       NIerr_buff[2048] ={'\0'};	
	char *markers[] = {"SGoHigh", "RGoHigh"};
	int i, j, iters;
	int wait;


	lsl_streaminfo trigger_info;
	lsl_streaminfo nidaq_send_info;
	lsl_streaminfo nidaq_receive_info;

	lsl_outlet trigger_outlet;
	lsl_outlet nidaq_send_outlet;
	lsl_outlet nidaq_receive_outlet;


	// set up lsl info
	trigger_info       = lsl_create_streaminfo("trigger", "Markers", 1, LSL_IRREGULAR_RATE, cft_string, "Markers");
	nidaq_send_info    = lsl_create_streaminfo("nidaq_send", "nidaq_send", 1, NISR, cft_double64, "NIDaq-ouput");
	nidaq_receive_info = lsl_create_streaminfo("nidaq_receive", "nidaq_receive", 1, NISR, cft_double64, "NIDaq-input");
	
	//setup outlets
	trigger_outlet       = lsl_create_outlet(trigger_info, 0, 360);
	nidaq_send_outlet    = lsl_create_outlet(nidaq_send_info, 0, 360);
	nidaq_receive_outlet = lsl_create_outlet(nidaq_receive_info, 0, 360);



	// set up the NIdaq objects
	// output
	DAQmxErrChk(DAQmxCreateTask("", &NIth_o));
	DAQmxErrChk(DAQmxCreateAOVoltageChan(NIth_o, "Dev1/ao0","",-10.0,10.0,DAQmx_Val_Volts,""));
	DAQmxErrChk (DAQmxCfgSampClkTiming(NIth_o,"OnboardClock",10000.0,DAQmx_Val_Rising,DAQmx_Val_HWTimedSinglePoint,1));

	// input
	DAQmxErrChk(DAQmxCreateTask("", &NIth_i));
	DAQmxErrChk(DAQmxCreateAIVoltageChan(NIth_i, "Dev1/ai0","",DAQmx_Val_RSE,-10.0,10.0,DAQmx_Val_Volts,NULL));
	DAQmxErrChk (DAQmxCfgSampClkTiming(NIth_i,"OnboardClock",10000.0,DAQmx_Val_Rising,DAQmx_Val_HWTimedSinglePoint,1));

	//occasionally a clock will be missed. This prevents errors from being thrown on NI-6321.
	//order of events is still preserved, by the nature of DAQmx_HWTimedSinglePoint
	DAQmxErrChk (DAQmxSetRealTimeConvLateErrorsToWarnings(NIth_o, 1));
	DAQmxErrChk (DAQmxSetRealTimeConvLateErrorsToWarnings(NIth_i, 1));
	
	DAQmxErrChk (DAQmxStartTask(NIth_o));	
	DAQmxErrChk (DAQmxStartTask(NIth_i));
	// prepare the loop	
	printf("Streaming . . .\n");

	iters = 500000; //
	j=0;
	i = 0;
	// do loop
	while(1)//(j++<iters)
	{

		i=0;
		wait = 0;

		while(i<10000)
		{
		
			NIdata_o = (i<500)? .2 : 0.0;
	   
			// tell the pin to go to the value
			DAQmxErrChk (DAQmxWriteAnalogF64(NIth_o, 1,1,10.0,DAQmx_Val_GroupByChannel,&NIdata_o,NULL,NULL));
			// get the time
			ts = lsl_local_clock();

			if(i==0)	//if this is the start of the cycle, send an on marker
			{		
				//printf("%s, %1.8f\n",markers[0], ts);
				lsl_push_sample_strt(trigger_outlet, &markers[0], ts);
			}

			lsl_push_sample_dt(nidaq_send_outlet, &NIdata_o, ts);

			// read off the feedback channel
			DAQmxErrChk(DAQmxReadAnalogF64(NIth_i,1,10.0,DAQmx_Val_GroupByChannel,&NIdata_i,1,&ctr,NULL));
			// push that data
			ts = lsl_local_clock();
			lsl_push_sample_dt(nidaq_receive_outlet, &NIdata_i, ts);
		

			if(NIdata_i>.1 && wait == 0)
			{

				lsl_push_sample_strt(trigger_outlet, &markers[1], ts);
				// only send this marker once per cycle
				wait++;
				
			}	   

			i++;
		}
		//printf("%f\n", NIdata_i);
	}

Error:
	if( DAQmxFailed(NIerr) )
		DAQmxGetExtendedErrorInfo(NIerr_buff,2048);
	
	if( NIth_o!=0 )  {
		/*********************************************/
		// DAQmx Stop Code
		/*********************************************/
		DAQmxStopTask(NIth_o);
		DAQmxClearTask(NIth_o);
	}

	if( NIth_i!=0 )  {
		/*********************************************/
		// DAQmx Stop Code
		/*********************************************/
		DAQmxStopTask(NIth_i);
		DAQmxClearTask(NIth_i);
	}

	if( DAQmxFailed(NIerr) )
		printf("DAQmx Error: %s\n",NIerr_buff);


	printf("End of program, press Enter key to quit\n");
	getchar();
		lsl_destroy_outlet(trigger_outlet);
	lsl_destroy_outlet(nidaq_send_outlet);
	lsl_destroy_outlet(nidaq_receive_outlet);

	lsl_destroy_streaminfo(trigger_info);
	lsl_destroy_streaminfo(nidaq_send_info);
	lsl_destroy_streaminfo(nidaq_receive_info);
	return 0;
}