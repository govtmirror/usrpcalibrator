/* -*- c++ -*- */

#define USRPCALIBRATOR_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "usrpcalibrator_swig_doc.i"

%{
#include "usrpcalibrator/bin_statistics_ff.h"
#include "usrpcalibrator/stitch_fft_segments_ff.h"
#include "usrpcalibrator/controller_cc.h"
#include "usrpcalibrator/skiphead_reset.h"
%}

%include "usrpcalibrator/bin_statistics_ff.h"
GR_SWIG_BLOCK_MAGIC2(usrpcalibrator, bin_statistics_ff);
%include "usrpcalibrator/stitch_fft_segments_ff.h"
GR_SWIG_BLOCK_MAGIC2(usrpcalibrator, stitch_fft_segments_ff);
%include "usrpcalibrator/controller_cc.h"
GR_SWIG_BLOCK_MAGIC2(usrpcalibrator, controller_cc);
%include "usrpcalibrator/skiphead_reset.h"
GR_SWIG_BLOCK_MAGIC2(usrpcalibrator, skiphead_reset);
