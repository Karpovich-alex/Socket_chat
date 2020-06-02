import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("127.0.0.1", 10001))
sock.listen(socket.SOMAXCONN)
#todo: asyncio
#todo: connection with client
#todo: create users database
#todo: message types
#todo: commands
#todo: raspberry?)
#todo: save logins
conn, addr = sock.accept()
# conn.settimeout(1)#timeout for connection
print('Conected client:', addr)
memory = dict()


def check_name(text, addr):
    ip = addr[0]
    port = addr[1]
    # sock.send(ip, "Добро пожаловать на супер чат! введите имя через 'name:'".encode('utf8'))
    a = 'Hello'
    socket.create_connection((ip, 10001),5).send(a.encode("utf8"))
    if text[:5] == 'name:':
        memory[ip] = text[5:].strip()
    else:
        if ip in memory:
            print('{id} > {mes}'.format(mes=data.decode('utf8'), id=memory[ip]))
        else:
            print('{id} > {mes}'.format(mes=data.decode('utf8'), id='unknown'))


while True:
    try:
        data = conn.recv(1024)
    except socket.timeout:
        print('close connection')
        break

    if not data:
        break
    check_name(data.decode('utf8'), addr)
conn.close()
sock.close()
