//===========================================================================
/*
    This file is part of the CHAI 3D visualization and haptics libraries.
    Copyright (C) 2003-2010 by CHAI 3D. All rights reserved.

    This library is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License("GPL") version 2
    as published by the Free Software Foundation.

    For using the CHAI 3D libraries with software that can not be combined
    with the GNU GPL, and for taking advantage of the additional benefits
    of our support services, please contact CHAI 3D about acquiring a
    Professional Edition License.

    \author    <http://www.chai3d.org>
    \author    Francois Conti
    \version   2.1.0 $Rev: 322 $
*/
//===========================================================================

//---------------------------------------------------------------------------
#ifndef CPrecisionClockH
#define CPrecisionClockH
//---------------------------------------------------------------------------
#include "extras/CGlobals.h"
//---------------------------------------------------------------------------

//===========================================================================
/*!
    \file       CPrecisionClock.h

    \brief
    <b> Timers </b> \n 
    High Precision Clock.
*/
//===========================================================================

//===========================================================================
/*!
	\class	    cPrecisionClock
    \ingroup    timers  

	\brief	
    cPrecisionClock provides a class to manage high-precision time 
    measurements. All measurements are computed in seconds unless
    otherwise-specified. \n cPrecisionClock behaves just like a real chronograph:  
	It can be started, stopped and restarted a later time. When the clock is running (ON),
	time is accumulated until the next stop event (OFF). The value of the clock can
	be read at any time by calling method getCurrentTimeSeconds(). When the clock
	is stopped (OFF), time is no longer accumulated.
*/
//===========================================================================
class cPrecisionClock
{
  public:

    //-----------------------------------------------------------------------
    // CONSTRUCTOR & DESTRUCTOR:
    //-----------------------------------------------------------------------
    
    //! Constructor of cPrecisionClock.
    cPrecisionClock();

    //! Destructor of cPrecisionClock.
    ~cPrecisionClock();


    //-----------------------------------------------------------------------
    // METHODS:
    //-----------------------------------------------------------------------

    //! Reset the clock to zero.
    void reset();

    //! Start counting time; optionally reset the clock to zero.
    double start(bool a_resetClock = false);

    //! Stop counting time; return the elapsed time.
    double stop();

    //! Return \b true if clock is currently \b on (clock is running), else return \b false (clock is paused).
    bool on() { return (m_on); };

    //! Read the current clock time (seconds).
    double getCurrentTimeSeconds();

    //! Set the period before a "timeout" occurs (you need to poll for this).
    void setTimeoutPeriodSeconds(double a_timeoutPeriod);

    //! Read the programmed timeout period
    double getTimeoutPeriodSeconds() { return (m_timeoutPeriod); }

    //! Returns \b true if a timeout has occurred.
    bool timeoutOccurred();

    //! Returns \b true if the high resolution CPU clock are available on this computer.
    bool highResolution() { return (m_highres); };

    //! If all you want is something that tells you the raw CPU time, this is your function...
    double getCPUTimeSeconds();

    //! For backwards-compatibility...
    double getCPUTime() { return getCPUTimeSeconds(); }

    //! For backwards-compatibility...
    double getCPUtime() { return getCPUTimeSeconds(); }

  private:

#if defined(_WIN32)
    //! Stores information about CPU high precision clock.
    LARGE_INTEGER m_freq;
#endif

    //! Time accumulated between previous calls to "start" and "stop".
    double m_timeAccumulated;

    //! CPU time when clock was started. Unit: seconds
    double m_timeStart;

    //! Timeout period. Unit: seconds
    double m_timeoutPeriod;

    //! clock time when timer was started. Unit: seconds
    double m_timeoutStart;

    //! If \b true, a  high precision CPU clock is available.
    bool m_highres;

    //! If \b true, the clock is currently \b on.
    bool m_on;
};

//---------------------------------------------------------------------------
#endif
//---------------------------------------------------------------------------
