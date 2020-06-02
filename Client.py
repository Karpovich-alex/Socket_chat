import threading
import socket
#todo: принимать сообщения сервер
try:
    sock=socket.create_connection(("127.0.0.1", 10001),5)
except socket.timeout:
    exit('Server not found')

text=str(input())
while text!='/e':
    try:
        sock.send(text.encode("utf8"))
    except socket.timeout:
        print("send data timeout")
    except socket.error as ex:
        print("send data error:", ex)
        break
    text = str(input())

sock.close()