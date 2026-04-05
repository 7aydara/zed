---
name: ping_test
description: Tests network connectivity by pinging an ip (do not use spaces)
arguments: ip_address
---
!`ping -n 4 ${ip_address}`
