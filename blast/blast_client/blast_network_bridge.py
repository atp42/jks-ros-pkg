#--------------------------------------------------------------------
#Copyright (c) 2015
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without 
#modification, are permitted provided that the following conditions 
#are met:
#  1. Redistributions of source code must retain the above copyright 
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above 
#     copyright notice, this list of conditions and the following 
#     disclaimer in the documentation and/or other materials 
#     provided with the distribution.
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
#"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
#LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
#FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
#COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
#INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
#HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
#ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
#ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#--------------------------------------------------------------------

import socket, threading, time, traceback, hashlib, sys, subprocess, os, json, random
import errno

def enc_str(s):
    return s.replace("%", "%p").replace("\n", "%n").replace(",", "%c")
def dec_str(s):
    return s.replace("%n", "\n").replace("%c", ",").replace("%p", "%")


class HashStore():
    def __init__(self, file_fun):
        self.lock = threading.Lock()
        self.file_fun = file_fun

    def safe_file(self, fn):
        if fn == "__root": 
            return
        if fn.find("__") != -1:
            raise Exception("You cannot have double underscores: " + str(fn))
        if not fn.replace("_", "").replace("-", "").isalnum():
            raise Exception("You must have an alphanumeric string with - and _: " + str(fn))
    
    def hash_file(self, a1, a2):
        return self.file_fun(a1, a2)

    def read_file(self, a1, a2):
        self.lock.acquire()
        fstr = ""
        try:
            fn = open(self.hash_file(a1, a2), "r")
            for l in fn: fstr += l
            fn.close()
        except:
            fstr = None
        self.lock.release()
        return fstr

    #Validates that a file that exists and that it has the correct hash
    def validate_file(self, a1, a2, ahash = None):
        fstr = self.read_file(a1, a2)
        if fstr == None:
            return False
        if ahash == None:
            return True
        hl = hashlib.sha256()
        hl.update(str(fstr))
        mh = str(hl.digest())
        return (mh == ahash)
        
    def write_file(self, a1, a2, content):
        self.lock.acquire()
        f = open(self.hash_file(a1, a2), "w")
        f.write(content)
        f.close()
        self.lock.release()
        
class ActionStore():
    def __init__(self, adir):
        self.actions_dir = adir
        self.libraries = {}
        self.hs = HashStore(self.action_file)
    def action_file(self, robot, action):
        self.hs.safe_file(robot)
        self.hs.safe_file(action)
        return self.actions_dir + "/" + robot + "__" + action + ".py"
    def validate_action(self, robot, action, ahash = None):
        return self.hs.validate_file(robot, action, ahash)
    def write_action(self, robot, action, content):
        return self.hs.write_file(robot, action, content)
    def read_action(self, robot, action):
        return self.hs.read_file(robot, action)
    def set_libraries(self, robot, action, libs):
        if not robot in self.libraries:
            self.libraries[robot] = {}
        if type(libs) == str or type(libs) == unicode:
            libs = [str(x) for x in json.loads(libs)]
        self.libraries[robot][action] = libs
    def get_libraries(self, robot, action):
        return self.libraries.get(robot, {}).get(action, [])

class LibraryStore():
    def __init__(self, ldir):
        self.libs_dir = ldir
        self.hs = HashStore(self.library_file)
    def library_file(self, robot, action):
        self.hs.safe_file(robot)
        self.hs.safe_file(action)
        return self.libs_dir + "/" + robot + "__" + action + ".py"
    def validate_library(self, robot, action, ahash = None):
        return self.hs.validate_file(robot, action, ahash)
    def write_library(self, robot, action, content):
        return self.hs.write_file(robot, action, content)
    def read_library(self, robot, action):
        return self.hs.read_file(robot, action)


class MapStore():
    def __init__(self, mdir):
        self.lock = threading.Lock()
        self.maps_dir = mdir
        self.map_cache = {}
        self.map_hash = {}
        self.map_resolution = {}
    
    def write_map(self, map_name, c, res):
        #TODO: validate map name
        self.lock.acquire()
        fn = open(self.maps_dir + "/" + map_name + ".pgm", "w")
        fn.write(c)
        fn.close()
        fn = open(self.maps_dir + "/" + map_name + ".txt", "w")
        fn.write(str(res))
        fn.close()
        if map_name in self.map_cache:
            del self.map_cache[map_name]
        if map_name in self.map_hash:
            del self.map_hash[map_name]
        if map_name in self.map_resolution:
            del self.map_resolution[map_name]
        self.load_map(map_name, no_lock = self.lock)

    def get_data(self, map_name):
        self.lock.acquire()
        if not map_name in self.map_resolution or not map_name in self.map_cache:
            self.load_map(map_name, no_lock = self.lock)
            self.lock.acquire()
        r = (self.map_resolution[map_name], self.map_cache[map_name])
        self.lock.release()
        return r
    
    def load_map(self, map_name, no_lock = False):
        if no_lock != False and no_lock != self.lock:
            raise Exception("You should not set the no_lock parameter")
        elif no_lock == False:
            self.lock.acquire()
        if map_name in self.map_cache and map_name in self.map_hash and map_name in self.map_resolution:
            rv = self.map_cache[map_name], self.map_hash[map_name], self.map_resolution[map_name]
            self.lock.release()
            return rv

        if not os.path.isfile(self.maps_dir + "/" + map_name + ".txt"):
            self.lock.release()
            return None, None, None
        if not os.path.isfile(self.maps_dir + "/" + map_name + ".pgm"):
            self.lock.release()
            return None, None, None
        try:
            #print "Read in", map_name
            fn = open(self.maps_dir + "/" + map_name + ".txt", "r")
            res = float(fn.read())
            fn.close()
            fn = open(self.maps_dir + "/" + map_name + ".pgm", "r")
            fd = [] 
            hl = hashlib.sha256()
            hl.update(str(res))
            while True:
                r = fn.read(128)
                if not r: break
                fd.append(r)
                hl.update(r)
            fn.close()
            md = "".join(fd)
            mh = str(hl.digest())
            self.map_cache[map_name] = md
            self.map_hash[map_name] = mh
            self.map_resolution[map_name] = res
            #print "Done"
            self.lock.release()
            return md, mh, res
        except:
            print "Could not open", map_name
            traceback.print_exc()
            self.lock.release()
            return None, None, None

class BlastNetworkBridge:
    def __init__(self, host, port, robot_name, robot_type, 
                 install_action, capability_cb,
                 map_store, action_store, library_store,
                 require_location = False):
        self.action_store = action_store
        self.library_store = library_store
        self.install_action = install_action
        self.robot_name = robot_name
        self.robot_type = robot_type
        self.require_location = require_location
        self.map_store = map_store
        self.capability_cb = capability_cb
        self.connection_lock = threading.Lock()
        self.alive = True
        self.host = host
        self.port = port
        self.action_id = 0
        self.thread = None
        self.error = False
        self.connect_fail = False
        self.action_callbacks = {}
        self.capabilities = {}
        self.SHUT_WR = socket.SHUT_WR
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.settimeout(0.001)
        try:
            # Connect to server and send data
            self.sock.connect((self.host, self.port))
        except:
            self.connect_fail = True
            self.error = "CONNECT FAIL"

    def action_start(self, action_robot_type, action_name, action_id, parameters, write_callback, capability_write):
        file_name = self.action_store.action_file(action_robot_type, action_name)
        if file_name == None: return None
        libs = self.action_store.get_libraries(action_robot_type, action_name)
        libf = []
        for lib in libs:
            if lib.find(".") == -1:
                #TODO: check if correct behavior!!! action_robot_type vs. robot_type
                libf.append(self.library_store.library_file(action_robot_type, lib))
            else:
                libf.append(self.library_store.library_file(lib.split(".")[0], lib.split(".")[1]))
        my_path = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(my_path + "/../blast_client")
        exec_path = my_path + "/../blast_client/blast_action_exec.py"
        cmd = ['python', '-u', exec_path, file_name, parameters] + libf
        exc = ActionExecutor(cmd, action_id, write_callback, capability_write)
        return exc.get_callback()
    
    def capability_write(self, aid, cap, fn, param):
        if not aid in self.action_callbacks:
            return "Gnull"
        do_send = True
        res = "null"
        if cap not in self.capabilities:
            self.capabilities[cap] = set()
        
        #Special logic for the start and stop function.
        if fn == "START":
            if len(self.capabilities[cap]) > 0:
                do_send = False
            if aid in self.capabilities[cap]: #Return false if already started
                res = "false"
            else:
                res = "true"
                self.capabilities[cap].add(aid)
                param = "null"
        elif fn == "STOP":
            if aid not in self.capabilities[cap]:
                res = "false"
                do_send = False
            else:
                self.capabilities[cap].remove(aid)
                res = "true"
                if len(self.capabilities[cap]) > 0:
                    do_send = False
        if do_send:
            try:
                res = self.capability_cb(cap, fn, param)
                res = json.dumps(res)
            except:
                print "Exception in capability"
                return "E" + traceback.format_exc()
        return "G" + res

    def write_data(self, data, terminate_action = None, total_stop = None):
        good = True
        #print "Writing data", data
        self.connection_lock.acquire()
        if terminate_action != None:
            #print "Terminating action", terminate_action
            if terminate_action in self.action_callbacks:
                del self.action_callbacks[terminate_action]
            for cap in self.capabilities:
                if terminate_action in self.capabilities[cap]:
                    self.capabilities[cap].remove(terminate_action)
                    if len(self.capabilities[cap]) == 0:
                        self.connection_lock.release()
                        self.capability_cb(cap, "STOP", "null")
                        self.connection_lock.acquire()
            if total_stop and False:
                self.stop()
        if not self.error and self.alive:
            try:
                self.sock.send(data)
            except:
                print "Send error!!!"
                traceback.print_exc()
                good = False
        else:
            print "Failed for error or alive", self.error, self.alive
            good = False
        self.connection_lock.release()
        if not good:
            print "We could not write data to the server!"
        #print "Done"
        return good

    def thread_runner(self):
        try:
            self.sock.send("BLAST_ROBOT_CONNECT\n")
            buff = ""
            print "Beginning reading"
            while self.alive and not self.error:
                if buff.find("\n") == -1:
                    try:
                        received = self.sock.recv(2*1024*2*2*2)
                    except socket.error, e:
                        err = e.args[0]
                        if err == 'timed out':
                            continue
                        else:
                            raise e
                    except KeyboardInterrupt:
                        self.stop()
                        continue
                    if received == None or received == False:
                        break
                    buff += received
                    #print "STPE", buff
                if buff.find("\n") != -1:
                    packet = buff[0:buff.find("\n")].strip()
                    buff = buff[buff.find("\n")+1:]
                    #print "Packet", packet[0:128]
                    self.connection_lock.acquire()
                    if packet.find("ERROR,") == 0:
                        self.error = "PACKET ERROR: " + packet[packet.find(",")+1:]
                    elif packet == "WAIT_NAME":
                        self.sock.send("ROBOT," + self.robot_name + "," + self.robot_type + "\n")
                    elif packet == "VALID_ROBOT":
                        self.sock.send("LIST_MAPS\n")
                    elif packet.find("ACTIONS") == 0:
                        ac_data = packet.split(",")[1:]
                        request_action = None
                        for i in range(len(ac_data)/4):
                            arobot, aaction = dec_str(ac_data[i*4]), dec_str(ac_data[i*4+1])
                            ahash, alibs = dec_str(ac_data[i*4+2]), dec_str(ac_data[i*4+3])
                            #print "We are trying action", arobot, aaction, ahash, alibs
                            self.action_store.set_libraries(arobot, aaction, alibs)
                            if not self.action_store.validate_action(arobot, aaction, ahash):
                                request_action = [arobot, aaction]
                                break
                        #Start the controller
                        print "ACTIONS", request_action
                        if self.error:
                            print "Error"
                            self.connection_lock.release()
                            break
                        if request_action != None:
                            self.sock.send("GET_ACTION," + enc_str(request_action[0]) + "," + enc_str(request_action[1]) + ",\n")
                        else:
                            print "Get Libs"
                            self.sock.send("LIST_LIBRARIES\n")
                    elif packet.find("LIBRARIES") == 0:
                        ac_data = packet.split(",")[1:]
                        request_action = None
                        for i in range(len(ac_data)/3):
                            arobot, aaction, ahash = dec_str(ac_data[i*3]), dec_str(ac_data[i*3+1]), dec_str(ac_data[i*3+2])
                            #print "We are trying action",
                            if not self.library_store.validate_library(arobot, aaction, ahash):
                                request_action = [arobot, aaction]
                                break
                        #Start the controller
                        print "LIBRARIES", request_action
                        if self.error:
                            print "Error"
                            self.connection_lock.release()
                            break
                        if request_action != None:
                            self.sock.send("GET_LIBRARY," + enc_str(request_action[0]) + "," + enc_str(request_action[1]) + ",\n")
                        elif self.require_location:
                            print "Wait loc"
                            self.sock.send("WAIT_LOCATION\n")
                        else:
                            print "Start!!!"
                            self.sock.send("START\n")
                    elif packet.find("ACTION,") == 0:
                        ac_data = packet.split(",")[1:]
                        actr = dec_str(ac_data[0])
                        actn = dec_str(ac_data[1])
                        code = dec_str(ac_data[2])
                        self.action_store.write_action(actr, actn, code)
                        self.sock.sendall("LIST_ACTIONS\n")
                    elif packet.find("LIBRARY,") == 0:
                        ac_data = packet.split(",")[1:]
                        actr = dec_str(ac_data[0])
                        actn = dec_str(ac_data[1])
                        code = dec_str(ac_data[2])
                        self.library_store.write_library(actr, actn, code)
                        self.sock.sendall("LIST_LIBRARIES\n")
                    elif packet.find("MAPS") == 0:
                        map_data = packet.split(",")[1:]
                        is_good = True
                        for i in range(len(map_data)/2):
                            map_name, hash_value = dec_str(map_data[i*2]), dec_str(map_data[i*2+1])
                            map_content, map_hash, map_resolution = self.map_store.load_map(map_name)
                            if not map_content or not map_hash:
                                print "Non-existant file", map_name
                                self.sock.send("GET_MAP," + map_name + "\n")
                                is_good = False
                                break
                            else:
                                if map_hash != hash_value:
                                    print "Invalid hash", map_name
                                    #print map_hash
                                    #print hash_value
                                    self.sock.send("GET_MAP," + enc_str(map_name) + "\n")
                                    is_good = False
                                    break
                        if is_good:
                            self.sock.send("LIST_ACTIONS\n")
                    elif packet.find("MAP,") == 0:
                        map_data = packet.split(",")
                        map_name = dec_str(map_data[1])
                        map_r = float(dec_str(map_data[2]))
                        map_c = dec_str(map_data[3])
                        print "Writing map", map_name, map_r
                        self.map_store.write_map(map_name, map_c, map_r)
                        self.sock.send("LIST_MAPS\n")
                    elif packet.find("STARTED") == 0:
                        self.connection_lock.release()
                        break
                    else:
                        self.error = "INVALID PACKET," + packet[0:128]
                    self.connection_lock.release()


            if self.error:
                print "System error, not starting second loop."
            else:
                print "-------------------Starting second loop-----------------------"
                while self.alive and not self.error:
                    if buff.find("\n") == -1:
                        try:
                            received = self.sock.recv(2*1024*2*2*2)
                        except socket.error, e:
                            err = e.args[0]
                            if err == 'timed out':
                                continue
                            else:
                                raise e
                        except KeyboardInterrupt:
                            self.stop()
                            continue
                        if received == None or received == False:
                            break
                        buff += received
                    if buff.find("\n") != -1:
                        packet = buff[0:buff.find("\n")].strip()
                        buff = buff[buff.find("\n")+1:]
                        self.connection_lock.acquire()
                        def is_int(x):
                            try:
                                int(x)
                                return True
                            except:
                                return False
                        if packet.find("START_ACTION,") == 0:
                            self.sock.send("STARTED_ACTION,"
                                           + str(self.action_id) + "\n")
                            self.action_callbacks[self.action_id] \
                                = self.action_start(packet.split(",")[1].strip(),
                                                    packet.split(",")[2].strip(),
                                                    self.action_id,
                                                    dec_str(packet.split(",")[3]),
                                                    self.write_data,
                                                    self.capability_write)
                            self.action_id += 1
                            self.connection_lock.release()
                        elif is_int(packet.split(",")[0]):
                            aid = int(packet.split(",")[0])
                            data = packet[packet.find(",")+1:]
                            #print "Send", aid, "<-", data
                            ac = self.action_callbacks.get(aid, None)
                            self.connection_lock.release()
                            if ac != None:
                                ac(dec_str(data))
                            elif aid > self.action_id:
                                self.error = "INVALID_ACTION," + str(aid)
                            else:
                                print "WARNING: message ignored from terminated action"
                        else:
                            self.error = "INVALID_PACKET," + packet
                            self.connection_lock.release()
        except:
            print "There was an exception in reading:"
            traceback.print_exc()
            self.error = "READ EXCEPTION"
        finally:
            try:
                self.sock.shutdown(self.SHUT_WR)
            except:
                pass
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
            self.alive = False

    def start(self):
        self.thread = threading.Thread(target=self.thread_runner)
        self.thread.start()

    def wait(self, check_fn = None):
        try:
            while self.alive:
                time.sleep(0.1)
                if check_fn:
                    if not check_fn():
                        print "Shutdown for external trigger"
                        break
        except:
            print "Wait interrupted"
            pass
        
    def __del__(self):
        self.stop()

    def stop(self):
        self.alive = False
        if self.sock:
            print "Socket shutdown"
            self.sock.shutdown(self.SHUT_WR)
            self.sock = None
        if self.thread:
            self.thread.join()
            self.thread = None
        

#['python', exec_path, py_file, json.dumps(json_prepare(parameters))],
class ActionExecutor():
    def __init__(self, start_command, action_id, write_callback, capability_callback):
        self.shutdown = False
        self.action_id = action_id
        self.write_callback = write_callback
        self.capability_callback = capability_callback
        port = 0
        self.socket = None
        while True:
            try:
                port = random.randint(10000, 30000)
                print "For ", start_command
                print port
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.bind(('127.0.0.1', port))
                start_command.append(str(port))
                break
            except:
                print "Error"
                traceback.print_exc()
                pass
        self.socket.listen(10)
        self.proc = subprocess.Popen(start_command,
                                     stdout=sys.stdout, 
                                     stdin=subprocess.PIPE,
                                     stderr=sys.stdout) #TODO logging output needs to be handled
        self.thread = threading.Thread(target=self.thread_run)
        self.thread.start()

    def get_callback(self):
        return self.write
    
    def thread_run(self):
        self.conn, self.addr = self.socket.accept()
        buff = ""
        while not self.shutdown:
            #result = self.proc.stdout.readline()
            #if result != "":
            #    print "Message", result
            if buff.find("\n") == -1:
                try:
                    nv = self.conn.recv(1024)
                except:
                    self.shutdown = True
                    continue
                if nv == "":
                    self.shutdown = True
                    continue
                buff += nv
                #print buff
            result = ""
            if buff.find("\n") != -1:
                result = buff[:buff.find("\n")]
                buff = buff[buff.find("\n")+1:]
                #print "We have result: " , result
            if result != "":
                if (result.find("CAPABILITY,") == 0):
                    data = result.split(",")
                    cap = dec_str(data[1])
                    fn = dec_str(data[2])
                    param = json.loads(dec_str(data[3]))
                    d = self.capability_callback(self.action_id, cap, fn, param)
                    self.write(enc_str(d) + "\n") #Write the capability result.
                else:
                    term = None
                    if result.strip().strip(",").strip() in ["TERMINATE", "TERMINATE_ALL"]:
                        print "Recieved an explicit terminate message", self.action_id
                        term = self.action_id
                    self.write_callback(str(self.action_id) + "," + enc_str(result) + "\n", terminate_action = term, 
                                        total_stop = (result.strip().strip(",").strip() == "TERMINATE_ALL"))
            else:
                if self.proc.poll() != None:
                    print "Action shutdown"
                    self.shutdown = True
                    self.write_callback(str(self.action_id) + ",TERMINATE%n\n", terminate_action = self.action_id)
                    #time.sleep(0.001)
        print "Thread shutdown"
        try:
            self.conn.close()
        except:
            print "Con could not be closed"
        try:
            self.socket.close()
        except:
            print "Socket could not be closed"
        print "Conn and socket closed"
        
    def write(self, data):
        if data == None:
            if not self.shutdown:
                self.shutdown = True
                self.proc.terminate()
            self.thread.join()
            return
        self.conn.send(data)
        #self.proc.stdin.write(data)
        #self.proc.stdin.flush()
        
        


def action_start(action_robot_type, action_name, action_id, parameters, write_callback, capability_write):
    print "Action!!!"
    def my_action(data):
        print data
    return my_action

def capability_callback(capability, command, parameters):
    print "Run capability command:", capability, command, parameter
    return "null"

def install_action(robot_type, action_name):
    print "Installing", robot_type, action_name, "(test - does nothing)"
    return True

if __name__ == '__main__' and len(sys.argv) > 1:
    def write_c(s):
        print "ACTION", s
    act = ActionExecutor(["sleep", "5"], 1, write_c, capability_callback)
    time.sleep(1.0)
    act.write(None)
elif __name__ == '__main__':
    map_store = MapStore("maps/")
    bnb = BlastNetworkBridge("localhost", 8080, "stair4", "pr2-cupholder",
                             action_start, install_action, capability_callback, map_store)
    bnb.start()
    bnb.wait()
    bnb.stop()
    if bnb.error:
        print "The system terminated with error", bnb.error









