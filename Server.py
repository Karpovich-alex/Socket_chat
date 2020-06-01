import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("192.168.0.136", 10001))
sock.listen(socket.SOMAXCONN)
#todo: asyncio
#todo: connection with client
#todo: create users database
#todo: message types
#todo: commands
#todo: raspberry?)
conn, addr = sock.accept()
print(addr[0])
memory = dict()


def check_name(text, addr):
    ip = addr[0]
    port = addr[1]
    # sock.send(ip, "Добро пожаловать на супер чат! введите имя через 'name:'".encode('utf8'))
    a = 'Hello'
    socket.create_connection((ip, 10001)).send(a.encode("utf8"))
    if text[:5] == 'name:':
        memory[ip] = text[5:].strip()
    else:
        if ip in memory:
            print('{id} > {mes}'.format(mes=data.decode('utf8'), id=memory[ip]))
        else:
            print('{id} > {mes}'.format(mes=data.decode('utf8'), id='unknown'))


while True:
    data = conn.recv(1024)

    if not data:
        break
    check_name(data.decode('utf8'), addr)
conn.close()
sock.close()
