#include <math.h>
#include <stdio.h>
#include <string.h>
#include <iostream>
#include <sstream>
#include "bosch_arm.h"
#include "cc2.h"
#include "daq.h"
#include "ros/ros.h"

using namespace std;
void BoschArm::initialize()
{
  //r1 = constants::r1;
  //r2 = constants::r2;
  L0 = constants::L0;
  L3=constants::L3;
  L4=constants::L4;
  L5=constants::L5;
  for (int i=0;i<16;i++)
    m2j[i] =constants::m2j[i];
  rad_per_count=constants::rad_per_count;

  setup626();
  time_now=S626_CounterReadLatch(constants::board0,constants::cntr_chan);
  time_last = time_now;
  time_now2= time_now;
  time_last2= time_now;
  home_offsets[0]=read_encoder(0) *rad_per_count;
  home_offsets[1]=read_encoder(1) *rad_per_count;
  home_offsets[2]=read_encoder(3) *rad_per_count;
  home_offsets[3]=read_encoder(2) *rad_per_count;
  for (int i=0;i<4;i++)
  {
    q[i]=0;
    ql[i]=0;
    v[i]=0;
    t_lims[i]=0.4*constants::t_max;
  }
  double vlim=constants::v_lim;
  v_lims[0]=vlim;
  v_lims[1]=2*vlim;
  v_lims[2]=2*vlim;
  v_lims[3]=2*vlim;
  zero_torques();
}

double BoschArm::convertToWallTime(uint16_t now,uint16_t last)
{
  uint16_t t = (now - last);
  return (double) t*constants::cnt2sec;
}
//get the hardware time
uint16_t BoschArm::getTime()
{
  return S626_CounterReadLatch(constants::board0,constants::cntr_chan);
}

void BoschArm::motor2JointPosition(const double* motors, double* joints)
{
  for (int i=0;i<4;i++)
  {
    joints[i]=0;
    for (int j=0;j<4;j++)
      joints[i]+=m2j[4*i+j]*motors[j];
  }
}

void BoschArm::joint2TipPosition(const double* joints, double* tip)
{
  double q1=joints[0];
  double q2=joints[1];
  double q3=joints[2];
  double q4=joints[3];

  tip[0]= - L4* (sin(q4) * (cos(q1) *cos(q3) - sin(q1) *sin(q2) *sin(q3)) + cos(q2) *cos(q4) *sin(q1))
          - L5* (cos(q4) * (cos(q1) *cos(q3) - sin(q1) *sin(q2) *sin(q3)) - cos(q2) *sin(q1) *sin(q4))
          - L3*cos(q2) *sin(q1);
  tip[1]=   L5*(sin(q2)*sin(q4) - cos(q2)*cos(q4)*sin(q3))
            - L4*(cos(q4)*sin(q2) + cos(q2)*sin(q3)*sin(q4))
            - L3*sin(q2);
  tip[2]=   L0
            - L4*(sin(q4)*(cos(q3)*sin(q1) + cos(q1)*sin(q2)*sin(q3)) - cos(q1)*cos(q2)*cos(q4))
            - L5*(cos(q4)*(cos(q3)*sin(q1) + cos(q1)*sin(q2)*sin(q3)) + cos(q1)*cos(q2)*sin(q4))
            + L3*cos(q1)*cos(q2);
}

void BoschArm::getJacobianJoint2Tip(const double* joints, double* jacobian)
{
  double q1=joints[0];
  double q2=joints[1];
  double q3=joints[2];
  double q4=joints[3];

  jacobian[0]=  L4*(sin(q4)*(cos(q3)*sin(q1) + cos(q1)*sin(q2)*sin(q3)) - cos(q1)*cos(q2)*cos(q4))
                + L5*(cos(q4)*(cos(q3)*sin(q1) + cos(q1)*sin(q2)*sin(q3)) + cos(q1)*cos(q2)*sin(q4))
                - L3*cos(q1)*cos(q2);
  jacobian[1]=  L4*(cos(q4)*sin(q1)*sin(q2) + cos(q2)*sin(q1)*sin(q3)*sin(q4))
                - L5*(sin(q1)*sin(q2)*sin(q4) - cos(q2)*cos(q4)*sin(q1)*sin(q3))
                + L3*sin(q1)*sin(q2);
  jacobian[2]=  L4*sin(q4)*(cos(q1)*sin(q3) + cos(q3)*sin(q1)*sin(q2))
                + L5*cos(q4)*(cos(q1)*sin(q3) + cos(q3)*sin(q1)*sin(q2));
  jacobian[3]=  L5*(sin(q4)*(cos(q1)*cos(q3) - sin(q1)*sin(q2)*sin(q3)) + cos(q2)*cos(q4)*sin(q1))
                - L4*(cos(q4)*(cos(q1)*cos(q3) - sin(q1)*sin(q2)*sin(q3)) - cos(q2)*sin(q1)*sin(q4));
  jacobian[4]=  0;
  jacobian[5]=  L5*(cos(q2)*sin(q4) + cos(q4)*sin(q2)*sin(q3))
                - L4*(cos(q2)*cos(q4) - sin(q2)*sin(q3)*sin(q4))
                - L3*cos(q2);
  jacobian[6]=- L5*cos(q2)*cos(q3)*cos(q4)
              - L4*cos(q2)*cos(q3)*sin(q4);
  jacobian[7]=  L4*(sin(q2)*sin(q4) - cos(q2)*cos(q4)*sin(q3))
                + L5*(cos(q4)*sin(q2) + cos(q2)*sin(q3)*sin(q4));
  jacobian[8]=- L4*(sin(q4)*(cos(q1)*cos(q3) - sin(q1)*sin(q2)*sin(q3)) + cos(q2)*cos(q4)*sin(q1))
              - L5*(cos(q4)*(cos(q1)*cos(q3) - sin(q1)*sin(q2)*sin(q3)) - cos(q2)*sin(q1)*sin(q4))
              - L3*cos(q2)*sin(q1);
  jacobian[9]=  L5*(cos(q1)*sin(q2)*sin(q4) - cos(q1)*cos(q2)*cos(q4)*sin(q3))
                - L4*(cos(q1)*cos(q4)*sin(q2) + cos(q1)*cos(q2)*sin(q3)*sin(q4))
                - L3*cos(q1)*sin(q2);
  jacobian[10]= L4*sin(q4)*(sin(q1)*sin(q3) - cos(q1)*cos(q3)*sin(q2))
                + L5*cos(q4)*(sin(q1)*sin(q3) - cos(q1)*cos(q3)*sin(q2));
  jacobian[11]= L5*(sin(q4)*(cos(q3)*sin(q1) + cos(q1)*sin(q2)*sin(q3)) - cos(q1)*cos(q2)*cos(q4))
                - L4*(cos(q4)*(cos(q3)*sin(q1) + cos(q1)*sin(q2)*sin(q3)) + cos(q1)*cos(q2)*sin(q4));
}
//   void joint2MotorPosition(const double* joints, double* motors)
//   {
//     for (int i=0;i<4;i++)
//     {
//       motors[i]=0;
//       for (int j=0;j<4;j++)
//         motors[i]+=j2m[4*i+j]*joints[j];
//     }
//   }

void BoschArm::safe_exit(const char* msg)
{
  close();
  ROS_ERROR(msg);
  //pthread_kill(servo, SIGTERM);
  exit(1);

}
void BoschArm::truncate(double &x, double max)
{
  if (x>max)
    x=max;
  if (x<-max)
    x=-max;
}
void BoschArm::enforce_safety()
{
  for (int i=0;i<4;i++)
  {
    if (fabs(v[i]) >v_lims[i])
      safe_exit("overspeed");
    if (fabs(torque[i]) >5*constants::t_max)
      safe_exit("torque command over 5 times max achievable");
    truncate(torque[i],t_lims[i]);
  }
//     double max[4];
//     int id=0;
//     double ratio=-1;
//     for(int i=0;i<4;i++)
//     {
//       if(ratio<torque[i]/t_lims[i])
//       {
//         ratio=torque[i]/t_lims[i];
//         id=i;
//       }
//     }
//     for(int i=0;i<4;i++)
//     {
//       truncate(torque[i],torque[i]/ratio);
//     }
}
void BoschArm::update()
{
  time_now2=S626_CounterReadLatch(constants::board0,constants::cntr_chan);
  q[0] = -read_encoder(0) *rad_per_count + home_offsets[0];
  q[1] = -read_encoder(1) *rad_per_count + home_offsets[1];
  q[2] = read_encoder(3) *rad_per_count - home_offsets[2];
  q[3] = read_encoder(2) *rad_per_count - home_offsets[3];
  dt=convertToWallTime(time_now2,time_last2);
  time_last2=time_now2;
  for (int i=0;i<4;i++)
  {
    v[i]= (q[i]-ql[i]) /dt;
    ql[i]=q[i];
  }
  enforce_safety();
  write_torque(0,torque[0]);
  write_torque(1,torque[1]);
  write_torque(2,torque[2]);
  write_torque(3,torque[3]);
}
void BoschArm::close()
{
  zero_torques();
  S626_InterruptEnable(constants::board0, FALSE);
  S626_CloseBoard(constants::board0);
  cout << "626 closed out." << endl;
}
void BoschArm::wait()
{
  do
  {
    time_now=getTime();
    //printf("%d\t",time_now);
  }
  while ((uint16_t)(time_now - time_last) < constants::cycle_counts);
  //printf("***\n");
  //printf("%d\n",(uint16_t)(time_now-time_last));
  time_last = time_now;
}
