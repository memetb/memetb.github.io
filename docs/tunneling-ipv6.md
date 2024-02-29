# Memet Bilgin's personal blog

 -- DRAFT -- 
 
## Tunneling ipv6 because... "why are you doing that?", "You're doing it wrong!😠"

Say you're like me, and you want to work on some server stuff, or you want to "project" your living room into the internet (i.e. you want to serve some content over ipv6)...

The use cases are too many to list, but mine were a dev environment for doing IaC stuff.

![Setup](assets/tunneling-ipv6.png "Setup")

## Premises:

1. Your home internet service doesn't support IPv6 and/or some thing about it ain't right...
1. You want to reach all of the internet, not only those who have IPv6
1. You don't want to pay for IP allocations, besides, weren't we promised IPv6 was "infinite"?
1. You don't want to, can't, don't have access to an ASN


## What you'll need:

1. Cloudflare account: I'm not shilling, but the services they offer for free are simply amazing
1. a VPS that gives you IPv6 allocations, however parsimonious*, every time you spin up a VM. I happen to use DO.

* this is important: many guides talk about /56 segments being handed to you by the benevolent overloards... but the setup here is good for something as small as an underouted /124 segment

## The setup

The setup is as follows: spin up the smallest VM, and add wireguard to it.


### Bastion config

```
[Interface]
Address = fd01::2:1/124
PrivateKey = YnV0IGRpZCB5b3Uga25vdz8gICAgIAo=
ListenPort = 1194

# home lan
[Peer]
PublicKey = SSBhbHNvIGRpZG4ndCBrbm93ISAgIAo=
AllowedIPs = fd01::2:0/124,fd01:1:1:1::d26:a000/124
```


```bash
root@bastion:~# alias ip6='ip -6 -c'
root@bastion:~# ip6 r
fd01:1:1:1::d26:a000/124 dev tun0 metric 1024 pref medium # manually added
fd01::2:0/124 dev tun0 proto kernel metric 256 pref medium
fe80::/64 dev eth0 proto kernel metric 256 pref medium
fe80::/64 dev eth1 proto kernel metric 256 pref medium
default via 2604:a880:cad:d0::1 dev eth0 metric 1024 onlink pref medium

root@bastion:~# ip6 a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
    inet6 ::1/128 scope host noprefixroute 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 fe80::94c3:11ff:fea4:5d27/64 scope link 
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 fe80::48e2:60ff:fef0:174/64 scope link 
       valid_lft forever preferred_lft forever
53: tun0: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1420 state UNKNOWN qlen 1000
    inet6 fd01::2:1/124 scope global 
       valid_lft forever preferred_lft forever
```


### Home router

On my home network, I dedicate VLAN6 for IPv6 traffic and dragons. I essentially treat this as a DMZ.

```
[Interface]
Address = fd01::2:2/124
PrivateKey = aGF2ZSB5b3Ugc3RpbGwgbm90IGxlYXJuZWQ/Cg==

[Peer]
PublicKey = dGhlcmUgaXMgbm8gYW5zd2VyIHRvIGl0IGFsbAo=
Endpoint = your-vm-slug.digitalocean.com:1194
AllowedIPs = fd02::2:0/124,::/0
PersistentKeepalive = 600 # important
```

```bash
root@home-router:/etc/wireguard# ip6 r
::1 dev lo proto kernel metric 256 pref medium
fd01::2:0/124 dev tun0 proto kernel metric 256 pref medium
fd01:1:1:1::d26:a000/124 dev eth0.6 proto kernel metric 256 pref medium # this is added by whom again?
fd02::2:0/124 dev tun0 metric 1024 pref medium
fe80::/64 dev eth1 proto kernel metric 256 pref medium
fe80::/64 dev eth0.6 proto kernel metric 256 pref medium
fe80::/64 dev eth0 proto kernel metric 1024 pref medium

root@home-router:/etc/wireguard# ip6 a 
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
5: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 fe80::389f:cc8b:5d44:534d/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever
54: eth0.6@eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 fd01:1:1:1::d26:a000/124 scope global 
       valid_lft forever preferred_lft forever
    inet6 fe80::c274:2bff:feff:f35f/64 scope link 
       valid_lft forever preferred_lft forever
60: tun0: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1420 state UNKNOWN qlen 1000
    inet6 fd01::2:2/124 scope global 
       valid_lft forever preferred_lft forever

```

### Nodes on router LAN

When I want a node to be projected to the wilds, I simply add the ULA translated address to the VLAN and away it goes.

```
# add this to my /etc/network/interfaces
auto eth0.6
iface eth0.6 inet6 static
        address fd01:1:1:1::d26:a004
        netmask 124
        gateway fd01:1:1:1::d26:a000

```

```bash
root@vanadium:~# ip6 a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
    inet6 ::1/128 scope host noprefixroute 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 fe80::3608:e1ff:fe59:d46/64 scope link 
       valid_lft forever preferred_lft forever
7: eth0.6@eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 fd01:1:1:1::d26:a004/124 scope global 
       valid_lft forever preferred_lft forever
    inet6 fe80::3608:e1ff:fe59:d46/64 scope link 
       valid_lft forever preferred_lft forever
       
root@vanadium:~# ip6 r
fd01:1:1:1::d26:a000/124 dev eth0.6 proto kernel metric 256 pref medium
fe80::/64 dev eth0 proto kernel metric 256 pref medium
fe80::/64 dev eth0.6 proto kernel metric 256 pref medium
default via fd01:1:1:1::d26:a000 dev eth0.6 metric 1024 onlink pref medium
       
```
