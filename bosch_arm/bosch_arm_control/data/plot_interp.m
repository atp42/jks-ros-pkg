t=data(:,1);
t=t-t(1);
t=t/max(t);
[t_o,d_o]=consolidate(t,data(:,9));
len_o=length(t_o);
t_step=max(t_o)/len_o;
data_int=interp1(t_o,d_o,t_step:t_step:max(t_o));
v=data_int(2:end)-data_int(1:end-1);
d=1/length(v);
figure;
plot(d:d:1,abs(fft(v)));