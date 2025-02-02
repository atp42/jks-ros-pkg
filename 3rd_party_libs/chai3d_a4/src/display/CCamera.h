//===========================================================================
/*
    Software License Agreement (BSD License)
    Copyright (c) 2003-2012, CHAI3D.
    (www.chai3d.org)

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:

    * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
    copyright notice, this list of conditions and the following
    disclaimer in the documentation and/or other materials provided
    with the distribution.

    * Neither the name of CHAI3D nor the names of its contributors may
    be used to endorse or promote products derived from this software
    without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
    FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
    COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
    BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
    ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE. 

    \author    <http://www.chai3d.org>
    \author    Francois Conti
    \author    Dan Morris
    \version   $MAJOR.$MINOR.$RELEASE $Rev: 403 $
*/
//===========================================================================

//---------------------------------------------------------------------------
#ifndef CCameraH
#define CCameraH
//---------------------------------------------------------------------------
#include "world/CGenericObject.h"
#include "math/CMaths.h"
#include "graphics/CImage.h"
//---------------------------------------------------------------------------
class cWorld;
//---------------------------------------------------------------------------

//===========================================================================
/*!
    \file       CCamera.h

    \brief 
    <b> Scenegraph </b> \n 
    Virtual Camera.
*/
//===========================================================================

//===========================================================================
/*!
      \class      cCamera
      \ingroup    scenegraph
      \brief      cCamera describes a virtual Camera located inside the world.
                  Its job in life is to set up the OpenGL projection matrix
                  for the current OpenGL rendering context.  The default camera
                  looks down the negative x-axis.  OpenGL folks may wonder why
                  we chose the negative x-axis... it turns out that's a better
                  representation of the standard conventions used in general
                  robotics.
*/
//===========================================================================
class cCamera : public cGenericObject
{
  friend class cWorld;

  public:
    
    //-----------------------------------------------------------------------
    // CONSTRUCTOR & DESTRUCTOR:
    //-----------------------------------------------------------------------

    //! Constructor of cCamera
    cCamera(cWorld* iParent);

    //! Destructor of cCamera
    virtual ~cCamera() {};


	//-----------------------------------------------------------------------
    // METHODS - MOUSE SELECTION:
	//-----------------------------------------------------------------------

    //! Get pointer to parent world.
    cWorld* getParentWorld() { return (m_parentWorld); }

    //! Query whether the specified position is 'pointing at' any objects in the world.
    virtual bool select(const int a_windowPosX, const int a_windowPosY,
                        const int a_windowWidth, const int a_windowHeight,
                        cCollisionRecorder& a_collisionRecorder,
						cCollisionSettings& a_collisionSettings);


	//-----------------------------------------------------------------------
    // METHODS - POSITION & ORIENTATION:
	//-----------------------------------------------------------------------

    //! Set the position and orientation of the camera.
    virtual bool set(const cVector3d& a_localPosition,
					 const cVector3d& a_localLookAt,
					 const cVector3d& a_localUp);

	//! Get the camera "look at" position vector for this camera.
    cVector3d getLookVector()  const { return m_localRot.getCol0(); }

	//! Get the  "up" vector for this camera.
    cVector3d getUpVector()    const { return m_localRot.getCol2(); }

	//! Get the "right direction" vector for this camera.
    cVector3d getRightVector() const { return m_localRot.getCol1(); }

    //! Projection matrix of camera.
    cTransform m_projectionMatrix;

	//! Modelview matrix of camera.
    cTransform m_modelviewMatrix;


	//-----------------------------------------------------------------------
    // METHODS - CLIPPING PLANES:
	//-----------------------------------------------------------------------

    //! Set near and far clipping planes.
    void setClippingPlanes(const double a_distanceNear, const double a_distanceFar);

    //! Get near clipping plane.
    double getNearClippingPlane() { return (m_distanceNear); }

    //! Get far clipping plane.
    double getFarClippingPlane() { return (m_distanceFar); }

    //! Automatically adjust back and front clipping planes.
    void adjustClippingPlanes();


	//-----------------------------------------------------------------------
    // METHODS - SHADOW CASTING:
	//-----------------------------------------------------------------------
    
	//! Enable or disable shadow rendering.
    void setUseShadowCasting(bool a_enabled);

    //! Read if shadow rendering is enabled.
    bool getUseShadowCastring() { return(m_useShadowCasting); }


	//-----------------------------------------------------------------------
    // METHODS - FIELD OF VIEW & OPTICS: 
	//-----------------------------------------------------------------------

    //! Set camera is orthographic mode
    void setOrthographicView(double a_viewWidth);

    //! Set field of view angle (in degrees).
    void setFieldViewAngle(double a_fieldViewAngle);

    //! Read field of view angle (in degrees).
    double getFieldViewAngle() { return (m_fieldViewAngle); }

	//! Return aspect ratio.
	double getAspectRatio();

    //! Set stereo focal length.
    void setStereoFocalLength(double a_stereoFocalLength);

    //! Get stereo focal length.
    double getStereoFocalLength() { return (m_stereoFocalLength); }

    //! Set stereo eye separation.
    void setStereoEyeSeparation(double a_stereoEyeSeparation);

    //! Get stereo eye separation.
    double getStereoEyeSeparation() { return (m_stereoEyeSeparation); }


	//-----------------------------------------------------------------------
    // METHODS - RENDERING AND IMAGING:
	//-----------------------------------------------------------------------

    //! Render the camera in OpenGL (i.e. set up the projection matrix)...
    virtual void renderView(const int a_windowWidth, const int a_windowHeight);

    //! Copy output image data to image structure.
    void copyImageData(cImage* a_image);

    //! Enable or disable additional rendering passes for transparency (see full comment).
    virtual void setUseMultipassTransparency(bool a_enabled);

    //! Read if multipass rendering is enabled.
    bool getUseMultipassTransparency() { return (m_useMultipassTransparency); }

    //! Enable or disable 3D stereo rendering.
    virtual void setUseStereo(bool a_enabled = true);

    //! Read if 3D stereo is enabled.
    bool getUseStereo() { return (m_useStereo); }

    //! Get the width of the current window display in pixels. 
    int getDisplayWidth() { return (m_lastDisplayWidth); }

    //! Get the height of the current window display in pixels. 
    int getDisplayHeight() { return (m_lastDisplayHeight); }

    //! Resets textures and displays for the world associated with this camera.
    virtual void onDisplayReset();


	//-----------------------------------------------------------------------
    // MEMBERS - FRONT AND BACK PLANES:
	//-----------------------------------------------------------------------

	/*
		These are special 'children' of the camera that are rendered independently of
		all other objects, intended to contain 2d objects only.  The 'back' scene is
		rendered before the 3d objects; the 'front' scene is rendered after the
		3d object.  These are made public variables to allow convenient access to
		the scenegraph management functions.

		These objects are rendered through an orthographic projection matrix, so the
		positive z axis faces the camera.  Depth is currently not used.  Lighting
		is disabled during rendering.
    */

	//! Front plane scenegraph which can be used to attach widgets.
	cWorld* m_frontLayer;

	//! Black plane scenegraph which can be used to attach widgets.
    cWorld* m_backLayer;


	//-----------------------------------------------------------------------
    // MEMBERS:
	//-----------------------------------------------------------------------

    protected:

    //! Parent world.
    cWorld *m_parentWorld;

    //! Distance to near clipping plane.
    double m_distanceNear;

    //! Distance to far clipping plane.
    double m_distanceFar;

    //! Field of view angle in degrees.
    double m_fieldViewAngle;

    //! Width of orthographic view
    double m_orthographicWidth;

    //! If \b true, then camera is in perspective mode. If \b false, then camera is of orthographic mode.
    bool m_perspectiveMode;

    //! If true, three rendering passes are performed to approximate back-front sorting (see long comment)
    bool m_useMultipassTransparency;

	//! If true, then use shadow casting.
	bool m_useShadowCasting;

    //! Focal length.
    double m_stereoFocalLength;

    //! Eye separation.
    double m_stereoEyeSeparation;

    //! If true, then use stereo display rendering.
    bool m_useStereo;

    //! last width size of the window.
    unsigned int m_lastDisplayWidth;

	//! last height size of the window.
    unsigned int m_lastDisplayHeight;

    //! if \b true then display reset has been requested.
    bool m_resetDisplay;


	//-----------------------------------------------------------------------
    // METHODS:
	//-----------------------------------------------------------------------

    protected:

    //! Render a 2d scene within this camera's view.
    void renderLayer(cGenericObject* a_graph, int a_width, int a_height);

	//! Verifies if shadow casting is supported on this hardware.
	bool isShadowCastingSupported();
};

//---------------------------------------------------------------------------
#endif
//---------------------------------------------------------------------------

