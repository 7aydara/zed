---
name: sys_info
description: Gets top 5 CPU processes to check system health
arguments: none
---
!`powershell -Command "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 name, cpu"`
