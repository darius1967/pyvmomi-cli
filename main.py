#!/usr/bin/python
import pyVim
from pyVim import connect
from pyVmomi import vim
import time
import argparse
import getpass
from pyVim.task import WaitForTask
l=time.localtime(time.time())

def get_args():
        parser = argparse.ArgumentParser(description='Arguments for talking to vCenter')
        parser.add_argument('-s', '--host',required=True,action='store',help='vcenter to connect to')
        parser.add_argument('-a', '--action',required=True,action='store',help='vcenter action to be performed:datastoreSystem,rescanallhba,getiscsilun,resethealthsystem,buildversion,getpNic,cpuinfo,meminfo,status,sensors,getcdp,vlans,ds_health,services,startssh,startesxshell,vswitch,clusters,getprofile,newprofile,delprofile,multipath,getwwn,getstolun,getsnap,hostinfo,hyperThread,newvswitch,addvlan,connection,umount_vmtool,cd_connected,respool,no_lockdown')
        parser.add_argument('-H', '--Host',required=False,action='store',help='Host to connect to')
        parser.add_argument('-u', '--user',required=True,action='store',help='User name to use')
        parser.add_argument('-p', '--password',required=False,action='store',help='Password to use')
        args = parser.parse_args()
        if not args.password:
                args.password = getpass.getpass(prompt='Enter password:')
        return args


def vmhosts(content):
        host_view = content.viewManager.CreateContainerView(content.rootFolder,[vim.HostSystem],True)
        obj = [host for host in host_view.view]
        host_view.Destroy()
        return obj


def create_snap(v):
        try:
                v.CreateSnapshot(memory=False,name="weekly snapshot",quiesce=False)
        except:
                pass

def get_vm_new(content):
        container = content.rootFolder
        vt = [vim.VirtualMachine]
        cnt_v = content.viewManager.CreateContainerView(container,vt,True)
        children = cnt_v.view
        for i, j in enumerate(children):
                if j.name.upper()=="SAP01812":
                        if j.snapshot <> None:
                                task = j.RemoveAllSnapshots_Task()
                                WaitForTask(task)
                                if task.info.state <> "success":
                                        return
                                else:
                                        time.sleep(2)
                        create_snap(j)

def storage(content):
        st_view = content.viewManager.CreateContainerView(content.rootFolder,[vim.Datastore],True)
        obj = [ s for s in st_view.view]
        st_view.Destroy()
        return obj

def get_clusters(cl):
        c=cl.viewManager.CreateContainerView(cl.rootFolder,[vim.ClusterComputeResource],True)
        for i in c.view:
                print i.name
                for j in i.host:
                        print "\t"+j.name

def get_template(content,p=0):
        pm = content.hostProfileManager
        if p==0:
                for i in pm.profile:
                        print i.name, i.config.annotation
        else:
                pp = [profile for profile in pm.profile]
                return pp

def delprofile(content):
        i=1
        while(i):
                pp = get_template(content,p=1)
                print "Alege profilul de sters:"
                for j,k in enumerate(pp):
                        print str(j+1)+"\t"+k.name
                i=input('Alege (0 pentru iesire):')
                if i>0:
                        pp[i-1].Destroy()

def get_conn_state(h):
        for i in h:
                print i.name,i.runtime.connectionState
def save_profile(content,h):
        l=time.localtime(time.time())
        fn=str(l.tm_year)+"_"+str(l.tm_mon)+"_"+str(l.tm_mday)+"_"+str(l.tm_hour)+"_"+str(l.tm_min)
        for i in range(0,len(h)):
                hpm = content.hostProfileManager
                spec = vim.profile.host.HostProfile.HostBasedConfigSpec()
                spec.name = 'profile-' + h[i].name
                spec.annotation = fn
                spec.enabled = False
                spec.host = h[i]
                spec.useHostProfileEngine = True
                try:
                        profile = hpm.CreateProfile(spec)
                        #xmlProfile = profile.ExportProfile()
                except vim.fault.DuplicateName:
                        print "Profile for "+h[i].name+" already exist"
                except:
                        print "Error for "+h[i].name

#def GetHostSw(hosts,v1):
#        hostSW = {}
        #f=open(fn_h,"a")
#        for host in hosts:
#               try:
#                       sw = host.config.network.vswitch
#                       hostSW[host] = sw
#               except:
#                       pass
        #f.close()
#        return hostSW

def GetHostSw(hosts,v1):
        hostSW = {}
        for host in hosts:
                try:
                        sw = host.config.network.vswitch
                        hostSW[host] = sw
                except:
                        print host.name+" "+host.runtime.connectionState
        return hostSW

def printHost(h):
        print "Hosts"
        print "----"
        for i in h:
                print str(i.name)+"|"+str(i.hardware.biosInfo.biosVersion)+"|"+str(i.hardware.biosInfo.releaseDate.year).strip()+"-"+str(i.hardware.biosInfo.releaseDate.month).strip()+"-"+str(i.hardware.biosInfo.releaseDate.day).strip()

#def printSW(h1,VCS):
#        hostSwitchDict = GetHostSw(h1,VCS)
#        for h,v in hostSwitchDict.items():
#               print h.name
#                for i in v:
#                        print i.name
#                       for j in i.pnic:
#                               print "\t - "+ j.split('-')[2]

def printSW(h1,VCS):
        hostSwitchDict = GetHostSw(h1,VCS)
        d_pg={}
        for h,v in hostSwitchDict.items():
                for inde in h.config.network.portgroup:
                        d_pg[inde.spec.name] = inde.spec.vlanId
                print h.name
                for i in v:
                        print i.name
                        for j in i.pnic:
                                print "\t - "+ j.split('-')[2]
                        for k in i.portgroup:
                                for i1 in d_pg.keys():
                                        if i1 in k:
                                                d_pg_i1=d_pg[i1]
                                #print "\t\t - "+k[k.index('-')+1:]+" - "+str(d_pg_i1)
                                print "\t\t - "+ k.split('-')[2]+" - "+str(d_pg[k.split('-')[2]])

def printIP(hosts,fn,v1):
        s='|'
        #fn=str(l.tm_year)+"_"+str(l.tm_mon)+"_"+str(l.tm_mday)+"_"+str(l.tm_hour)+"_"+str(l.tm_min)+"_"+str(l.tm_sec)
        f=open(fn,"a")
        #f.write(v1+'\n')
        hostSwitchDict = GetHostSw(hosts,v1)
        for i in hostSwitchDict.items():
#               print i[0].name
                for v in i[0].config.network.vnic:
#                       print i[0].name, v.device, v.spec.ip.ipAddress, v.spec.mac, v.spec.mtu, v.portgroup
                        l1=v1+s+i[0].name+s+v.device+s+v.spec.ip.ipAddress+s+v.spec.mac+s+str(v.spec.mtu)+s+v.portgroup+'\n'
                        f.write(l1)
        f.close()

def get_vm(content,fn):
        container = content.rootFolder
        vt = [vim.VirtualMachine]
        cnt_v = content.viewManager.CreateContainerView(container,vt,True)
        children = cnt_v.view
        f=open(fn,"a")
        for i in children:
                l1=''
                #l1=i.summary.config.name+"|"+str(i.summary.config.guestId)+'|'+i.summary.runtime.host.name+'|'+str(i.summary.config.numCpu)+'|'+str(i.summary.config.memorySizeMB)+'MB|'+str(i.summary.guest.ipAddress)+'|'+i.summary.runtime.powerState+'|'+i.storage.perDatastoreUsage[0].datastore.name+'|'+i.storage.perDatastoreUsage[0].datastore.summary.type+'\n'
                try:
                        l1=i.summary.config.name+"|"+str(i.summary.config.guestId)+'|'+i.summary.runtime.host.name+'|'+str(i.summary.config.numCpu)+'|'+str(i.summary.config.memorySizeMB)+'MB|'+str(i.summary.guest.ipAddress)+'|'+i.summary.runtime.powerState
                except:
                        pass
                try:
                        a=i.storage.perDatastoreUsage[0].datastore.name
                        l1=l1+'|'+a
                except:
                        pass
                try:
                        a=i.storage.perDatastoreUsage[0].datastore.summary.type
                        l1=l1+'|'+a
                except:
                        pass
                l1=l1+"\n"
                f.write(l1)
                for j in i.guest.net:
                        #print i.summary.config.name
                        if len(j.ipAddress)>0:
                                l2 = i.summary.config.name+"|"+j.ipAddress[0]+"|"+str(j.network)+"|"+str(j.macAddress)+'\n'
                                f.write(l2)

def get_hyperThread(h):
        for i in h:
                try:
                        print i.name,i.config.hyperThread.active
                except:
                        print i.name+" - can not determine hyperThread"

def se_vm(c,ip):
        searcher = c.content.searchIndex
        vm = searcher.FindByIp(ip=ip, vmSearch=True)
        try:
                print vm.config.name
        except:
                print "not found"

def get_fn():
        fn=str(l.tm_year)+"_"+str(l.tm_mon)+"_"+str(l.tm_mday)+"_"+str(l.tm_hour)+"_"+str(l.tm_min)+"_"+str(l.tm_sec)
        return fn

def set_custom_v(v):
        cfm=my_cluster.content.customFieldsManager
        cfm.AddCustomFieldDef(name=proba,moType=vim.VirtualMachine)
        v.setCustomValue(key=proba,value=Proba)

def h_storage(hosts):
        for i in hosts:
                try:
                        a=i.summary.runtime.healthSystemRuntime.hardwareStatusInfo.storageStatusInfo
                        for j in a:
                                print i.name+'|'+j.name+'|'+j.status.key
                except:
                        print i.name+'|'+'no_info'
def abc(c):
        for i in c.childEntity:
                print i.name
                print "----"
                try:
                        for k in i.hostFolder.childEntity:
                                for j in k.resourcePool.resourcePool:
                                        print j.name
                                #a=GetResourcePools(k.resourcePool)
                                #for j in a:
                                        #print j.name
                except:
                        pass

def h_status(hosts,v):
        for i in hosts:
                print v,i.name,i.summary.overallStatus

def h_sensor(hosts):
        for i in hosts:
                for j in i.summary.runtime.healthSystemRuntime.systemHealthInfo.numericSensorInfo:
                        print i.name,j.name,j.healthState.key

def get_conn_state(h):
#get host connection state
        for i in h:
                print i.name,i.runtime.connectionState

def h_cpu_info(h):
#print host cpu sockets,cores,threads
        print "Host     Sockets Cores   Threads"
        print "--------------------------------"
        for i in h:
                print i.name,i.hardware.cpuInfo.numCpuPackages,i.hardware.cpuInfo.numCpuCores,i.hardware.cpuInfo.numCpuThreads

def h_mem_info(h):
#print host memory
        for i in h:
                print i.name,sizetr(i.hardware.memorySize)

def sizetr(x):
        for i in ['b','k','M','G']:
                if x<1024:
                        return str(x)+i
                else:
                        x=x/1024
        return str(x)+"T"

#def get_build_ver(h):
#        for i in h:
#                print i.name,i.summary.host.config.product.build,i.summary.host.config.product.name

def get_build_ver(h):
        for i in h:
                try:
                        a=i.config.product
                        print i.name,i.config.product.build,i.config.product.name,i.config.product.version
                except:
                        print i.name+" nu are product"

#def get_pnic(h):
#        for j in h:
#                for i in j.config.network.pnic:
#                        try:
#                                A=i.linkSpeed.speedMb
#                        except:
#                                A="unset"
#                        finally:
#                                print j.name,i.device,i.pci,i.driver,A

def get_pnic(h,c=0):
        d={}
        for j in h:
                for i in j.config.network.pnic:
                        try:
                                A=i.linkSpeed.speedMb
                                d[i.device]=i.linkSpeed.speedMb
                        except:
                                A="unset"
                                d[i.device]="unset"
                        finally:
                                if c==0:
                                        print j.name,i.device,i.pci,i.driver,A
        if c==1:
                return d

def no_lockdown(h):
        for i in h:
                print i.name
                if i.runtime.connectionState=="connected":
                        try:
                                i.ExitLockdownMode()
                        except Exception as E:
                                print E.msg

def get_storage_lun(h):
        for i in h:
                print "Name    | State    | Lun    | Adapter"
                print "-------------------------------------"
                try:
                        i.config.storageDevice
                        for j in i.config.storageDevice.multipathInfo.lun:
                                for k in j.path:
                                        try:
                                                print k.name, k.state, k.lun.split('-')[2], k.adapter
                                        except:
                                                pass
                except:
                        pass

def get_wwn(h):
        print "Host\t|Model\t|nodeWorldWideName\tportWorldWideName"
        print "---------------------------------------------------"
        for i in h:
                try:
                        i.config.storageDevice
                        for j in i.config.storageDevice.hostBusAdapter:
                                try:
                                        a=j.nodeWorldWideName
                                        b=j.portWorldWideName
                                        print i.name,j.model, "%x" % a, "%x" % b
                                except:
                                        pass
                except:
                        pass

def get_cdp(h,v):
        for host in h:
                if host.runtime.connectionState=="connected":
                        networkSystem = host.configManager.networkSystem
                        if networkSystem is None:
                                continue
                        if not networkSystem.capabilities.supportsNetworkHints:
                                continue
                        for hint in networkSystem.QueryNetworkHint():
                                if hint.connectedSwitchPort:
                                        print v,host.name,hint.device, hint.connectedSwitchPort.devId,hint.connectedSwitchPort.portId,hint.connectedSwitchPort.vlan,hint.connectedSwitchPort.mtu
                else:
                        print v+" "+host.name+" "+host.runtime.connectionState

def get_vmnic_vlan(h):
        for host in h:
                networkSystem = host.configManager.networkSystem
                if networkSystem is None:
                        continue
                if not networkSystem.capabilities.supportsNetworkHints:
                        continue
                for hint in networkSystem.QueryNetworkHint():
                        #if hint.connectedSwitchPort:
                        for i in hint.subnet:
                                #print host.name,hint.device, "VLAN",i.vlanId, i.ipSubnet
                                print host.name+' '+hint.device+' '+"VLAN"+str(i.vlanId)+' '+i.ipSubnet

def get_iscsi(h):
#listeaza iscsi LUN
        for i in h:
                for j in i.configManager.storageSystem.storageDeviceInfo.scsiLun:
                        if "iSCSI Disk" in j.displayName:
                                print i.name+" "+ j.canonicalName+" "+ j.displayName


def scanhba(h):
#scaneaza hba
        for i in h:
                i.configManager.storageSystem.RescanAllHba()

def get_datastoreSystem(h):
        for i in h:
                for j in i.configManager.datastoreSystem.datastore:
                        if j.summary.type == 'VMFS':
                                for k in j.info.vmfs.extent:
                                        try:
                                                print "vmfs ",i.name,j.info.name,k.diskName
                                        except:
                                                pass
                        else:
                                if j.summary.type == 'NFS':
                                                try:
                                                        print "nas ",i.name,j.info.name,j.info.nas.remoteHost,j.info.nas.remotePath
                                                except:
                                                        pass

def umount_tool_ins(h):
        for i in h:
                for j in i.vm:
                        if j.summary.runtime.toolsInstallerMounted:
                                #j.UnmountToolsInstaller()
                                print j.name

def list_cd_connected(h):
        sep="|"
        for j in h:
                for k in j.vm:
                        for i in k.config.hardware.device:
                                try:
                                        if "CD" in i.deviceInfo.label:
                                                if i.connectable.connected == True:
                                                #print k.name+sep+i.deviceInfo.label+sep+i.deviceInfo.summary+sep+str(i.deviceInfo.connectable.connected)+sep+i.backing.filename+sep+i.backing.datastore
                                                        print k.name+sep+i.deviceInfo.label+sep+i.deviceInfo.summary+sep+i.backing.datastore.name+sep
                                except:
                                        pass

def xxx(h):
        for i in h:
                if i.runtime.connectionState=="connected":
                        for j in i.config.storageDevice.multipathInfo.lun:
                                print "LUN: ",j.id, j.lun
                                x1=' '
                                x2=' '
                                for k in j.path:
                                        if isinstance(k.transport,vim.host.InternetScsiTargetTransport):
                                                x1=k.transport.iScsiName
                                                if len(k.transport.address)>0:
                                                        x2=k.transport.address[0]
                                                else:
                                                        x2='empty'
                                        elif isinstance(k.transport,vim.host.FibreChannelTargetTransport):
                                                x1=k.transport.portWorldWideName
                                                x2=k.transport.nodeWorldWideName
                                        print "\t",k.adapter,k.isWorkingPath,k.pathState,x1,x2
                else:
                        print i.runtime.connectionState

def resethealthsys(h):
        for i in h:
                i.configManager.healthStatusSystem.ResetSystemHealthInfo()
                i.configManager.healthStatusSystem.RefreshHealthStatusSystem()

def newvswitch(h):
        vswitch_spec = vim.host.VirtualSwitch.Specification()
        vswitch_spec.numPorts = 1024
        vswitch_spec.mtu = 9000
        new_vswitch_name = raw_input('vSwitch name=')
        nic_name = raw_input('Nic name (comma delimited)=')
        vswitch_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=nic_name.split(','))
        for host in h:
                try:
                        task = host.configManager.networkSystem.AddVirtualSwitch(new_vswitch_name,vswitch_spec)
                        WaitForTask(task)
                        add_port_grp(host)
                except Exception, e:
                        try:
                                print e.msg
                        except:
                                print e

def connState(h):
        for i in h:
                print i.name,i.runtime.connectionState
def printSW1(h1,VCS):
        hostSwitchDict = GetHostSw(h1,VCS)
        d_pg={}
        for h,v in hostSwitchDict.items():
                for inde in h.config.network.portgroup:
                        d_pg[inde.spec.name] = inde.spec.vlanId
                l=[]
                l.append(h)
                d_pnic=get_pnic(l,1)
                print h.name
                for i in v:
                        print i.name
                        for j in i.pnic:
                                print "\t - "+ j.split('-')[2]+" -- speed "+str(d_pnic[j.split('-')[2]])
                        for k in i.portgroup:
                                print "\t\t - "+ k.encode('utf-8').split('key-vim.host.PortGroup-')[1]+" - "+str(d_pg[k.encode('utf-8').split('key-vim.host.PortGroup-')[1]])

def DS(d,v1):
        s=" | "
        if d.overallStatus<>"green":
                #if d.declaredAlarmState.overallStatus=="yellow" or d.declaredAlarmState.overallStatus=="red":
                        #d.declaredAlarmState.alarm.info.description
                for i in d.declaredAlarmState:
                        if i.overallStatus=="yellow" or i.overallStatus=="red":
                                print v1+s+d.name+s+i.alarm.info.description+s+i.overallStatus+s+str(i.time)[:str(i.time).index('.')]
# metode pentru ds: RefreshDatastore, RefreshDatastoreStorageInfo, RefreshStorageInfo

def printHost(h):
        print "Hosts | biosVersion | Date | Model | Vendor | Serial no | UUID"
        print "----"
        for i in h:
                try:
                        print str(i.name)+"|"+str(i.hardware.biosInfo.biosVersion)+"|"+str(i.hardware.biosInfo.releaseDate.year).strip()+"-"+str(i.hardware.biosInfo.releaseDate.month).strip()+"-"+str(i.hardware.biosInfo.releaseDate.day).strip()+"|"+i.hardware.systemInfo.model+"|"+i.hardware.systemInfo.vendor+"|"+i.hardware.systemInfo.otherIdentifyingInfo[1].identifierValue+"|"+i.hardware.systemInfo.uuid
                except:
                        print str(i.name)+"|"+str(i.hardware.biosInfo.biosVersion)+"|"+str(i.hardware.biosInfo.releaseDate.year).strip()+"-"+str(i.hardware.biosInfo.releaseDate.month).strip()+"-"+str(i.hardware.biosInfo.releaseDate.day).strip()+"|"+i.hardware.systemInfo.model+"|"+i.hardware.systemInfo.vendor+"|"+" "+"|"+i.hardware.systemInfo.uuid

def get_services(h):
        s=" | "
        for j in h:
                if j.runtime.connectionState=="connected":
                        print j.name
                        print "--------------------------"
                        for i in j.configManager.serviceSystem.serviceInfo.service:
                                print i.key+s+str(i.running)+s+i.policy+s+i.label
                        print "--------------------------"
                else:
                        print j.name+" "+j.runtime.connectionState

def startssh(h):
        for j in h:
                if j.runtime.connectionState=="connected":
                        for i in j.configManager.serviceSystem.serviceInfo.service:
                                if i.key=="TSM-SSH":
                                        if not i.running:
                                                #j.configManager.serviceSystem.StartService("TSM")
                                                j.configManager.serviceSystem.StartService("TSM-SSH")
                                        if i.policy != "on":
                                                j.configManager.serviceSystem.UpdateServicePolicy("TSM-SSH","on")
                                                print "Policy for TSM-SSH is on"

def startesxshell(h):
        for j in h:
                if j.runtime.connectionState=="connected":
                        for i in j.configManager.serviceSystem.serviceInfo.service:
                                if i.key=="TSM":
                                        if not i.running:
                                                j.configManager.serviceSystem.StartService("TSM")
                                        if i.policy != "on":
                                                j.configManager.serviceSystem.UpdateServicePolicy("TSM","on")
                                                print "Policy for ESXShell is on"

def main():
        printDatastore = True
        aktion=["datastoreSystem","rescanallhba","getiscsilun","resethealthsystem","buildversion","getpNic","cpuinfo","meminfo","status","sensors","getcdp","vlans","ds_health","services","startssh","startesxshell","vswitch","clusters","getprofile","newprofile","delprofile","multipath","getwwn","getsnap","hostinfo","hyperThread","addvlan","newvswitch","connection","getstolun","umount_vmtool","cd_connected","respool","no_lockdown"]
        #fn_v="vms_"+get_fn()
        #fn_h="hosts_"+get_fn()
        args = get_args()
        if args.action not in aktion:
                print "-h for help"
        P=args.password
        u=args.user
        #if args.host=="all":
        #        vc=["defthwa96gdv00.vdi.siemens.com", "defthwa908xvsh.vdi.siemens.com", "defthw900djv01.vdi.siemens.com", "defthwa908rvsh.vdi.siemens.com","defthwa908svsh.vdi.siemens.com", "defthwa908tvsh.vdi.siemens.com", "defthwa908uvsh.vdi.siemens.com", "defthwa908vvsh.vdi.siemens.com", "vca-65.vdi.siemens.com","sgsgpk0v061srv.vdi.siemens.com"]
        #else:
        vc=[i for i in args.host.split(',')]
        for v in vc:
                try:
                        my_cluster = connect.ConnectNoSSL(v, 443, u, P)
                        content = my_cluster.RetrieveContent()
                        hosts = vmhosts(content)
                        if args.Host is not None:
                                #hosts=filter(lambda x: x.name in args.Host.split(','), hosts)
                                hosts=filter(lambda x: x.name in [ lo.lower() for lo in args.Host.split(',') ] or x.name in [ lo.upper() for lo in args.Host.split(',') ], hosts)
                        if args.action=="datastoreSystem":
                                get_datastoreSystem(hosts)
                        elif args.action=="getiscsilun":
                                get_iscsi(hosts)
                        elif args.action=="umount_vmtool":
                                umount_tool_ins(hosts)
                        elif args.action=="respool":
                                abc(content.rootFolder)
                        elif args.action=="no_lockdown":
                                no_lockdown(hosts)
                        elif args.action=="rescanallhba":
                                scanhba(hosts)
                        elif args.action=="connection":
                                connState(hosts)
                        elif args.action=="hostinfo":
                                printHost(hosts)
                        elif args.action=="clusters":
                                get_clusters(content)
                        elif args.action=="getsnap":
                                get_vm_new(content)
                        elif args.action=="resethealthsystem":
                                resethealthsys(hosts)
                        elif args.action=="buildversion":
                                get_build_ver(hosts)
                        elif args.action=="getwwn":
                                get_wwn(hosts)
                        elif args.action=="getpNic":
                                get_pnic(hosts)
                        elif args.action=="getstolun":
                                get_storage_lun(hosts)
                        elif args.action=="multipath":
                                xxx(hosts)
                        elif args.action=="getprofile":
                                get_template(content)
                        elif args.action=="newprofile":
                                save_profile(content,hosts)
                        elif args.action=="newvswitch":
                                newvswitch(hosts)
                        elif args.action=="delprofile":
                                delprofile(content)
                        elif args.action=="cd_connected":
                                list_cd_connected(hosts)
                        elif args.action=="services":
                                get_services(hosts)
                        elif args.action=="startesxshell":
                                startesxshell(hosts)
                        elif args.action=="startssh":
                                startssh(hosts)
                        elif args.action=="vswitch":
                                printSW1(hosts,v)
                        elif args.action=="cpuinfo":
                                h_cpu_info(hosts)
                        elif args.action=="meminfo":
                                h_mem_info(hosts)
                        elif args.action=="status":
                                h_status(hosts,v)
                        elif args.action=="hyperThread":
                                get_hyperThread(hosts)
                        elif args.action=="sensors":
                                h_sensor(hosts)
                        elif args.action=="vlans":
                                get_vmnic_vlan(hosts)
                        elif args.action=="ds_health":
                                for datacenter in content.rootFolder.childEntity:
                                        if printDatastore:
                                                if isinstance(datacenter, vim.Folder):
                                                        continue
                                                datastores = datacenter.datastore
                                                for ds in datastores:
                                                        DS(ds,v)
                        elif args.action=="getcdp":
                                print "VCENTER,HOST,DEVICE,SwitchId,SwitchPort,VLAN,MTU"
                                print "-------------------------------------------------"
                                get_cdp(hosts,v)
                        connect.Disconnect(my_cluster)
                except:
                        print "Connection error for "+v

if __name__ == "__main__":
        main()
