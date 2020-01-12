import subprocess

p = subprocess.Popen('curl -s ifconfig.me',shell=True,stdout=subprocess.PIPE)
d = subprocess.Popen('Echo %computername%',shell=True,stdout=subprocess.PIPE)

ip=p.stdout.read()
name=d.stdout.read()

decodedIp=[ip.decode('utf-8')]
decodedName=[name.decode('utf-8')]

print('IP = ', decodedIp[0])

print('PC name = ', decodedName[0])