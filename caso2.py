#!/usr/bin_/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call


class MyNetwork():

    def createSwitches(self, net, n):

        info( '* Adding controller\n' )
        info( '* Add switches\n')
    
        switches, lan_switches, wan_switches = [], [], []
        
        # create switches
        for i in range(1, n+1):

            s_lan = net.addSwitch(f's{i}_lan', cls=OVSKernelSwitch, failMode='standalone')
            w_lan = net.addSwitch(f's{i}_wan', cls=OVSKernelSwitch, failMode='standalone')
            lan_switches.append(s_lan)
            wan_switches.append(w_lan)
        
        switches.append(lan_switches)
        switches.append(wan_switches)

        return switches


            
    def create_router(self, net, n):

        routers = []
        base = 6

        r_central = net.addHost('r_central', cls=Node, ip='192.168.100.6/29')
        routers.append(r_central)

        for i in range(1,n+1):
            base += 8
            router = net.addHost(f'r{i}', cls=Node, ip=f'10.0.{i}.1/24')
            routers.append(router)

        for r in routers:
            r.cmd('sysctl -w net.ipv4.ip_forward=1')
        
        return routers

    
    def create_hosts(self, net, n):

        info( '* Add hosts\n')

        hosts = []
        base = 0

        for i in range(n):
            base += 1
            host = net.addHost(f'h{i}', cls=Host, ip=f'10.0.{base}.254/24', defaultRoute=f'via 10.0.{i+1}.1')
            hosts.append(host)
        
        return hosts



    def create_links(self, routers, lan_sw, wan_sw, hosts, net, n):
        
        info( '* Add links\n')

        eth = 0
        base = -2
        wan_count = 1

        for s in wan_sw:
            net.addLink(routers[0], s, intfName1=f'r_central-eth{eth}', params1={ 'ip' : f'192.168.100.{base+8}/29' })
            eth += 1
            base += 8

        for i in range(1, n+1):
            net.addLink(routers[i], lan_sw[i-1], intfName1=f'r{i}-eth0', params1={ 'ip' : f'10.0.{i}.1/24' })
            net.addLink(routers[i], wan_sw[i-1], intfName1=f'r{i}-eth1', params1={ 'ip' : f'192.168.100.{wan_count}/29' })
            wan_count += 8

        for i in range(n):
            net.addLink(hosts[i], lan_sw[i])
   
        return


    def routing_table(self, n, net):

        info( '* Starting switches\n')
        base_ip = 1
    
        for i in range(n):
            net['r_central'].cmd(f'ip route add 10.0.{i+1}.0/24 via 192.168.100.{base_ip}')

            for j in range(n):
                net[f'r{i+1}'].cmd(f'ip route add 10.0.{j+1}.0/24 via 192.168.100.{base_ip+5}')
                
            base_ip += 8

        return


    def myNetwork(self, n):
        
        net = Mininet( topo=None,
                    build=False,
                    ipBase='10.0.0.0/8')

        # create switches
        switches = self.createSwitches(net, n)
        
        # create routers
        routers = self.create_router(net, n)

        # create hosts
        hosts = self.create_hosts(net, n)

        # create links
        self.create_links(routers, switches[0], switches[1], hosts, net, n)
        

        info( '* Starting network\n')
        net.build()
        info( '* Starting controllers\n')
        for controller in net.controllers:
            controller.start()

        info( '* Starting switches\n')

        net.start()

        # create routing table  
        self.routing_table(n, net)

       
        CLI(net)
        net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    my_net = MyNetwork()
    my_net.myNetwork(6)

    