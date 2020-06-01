import socket

sock=socket.socket()
sock.connect(("192.168.0.136", 10001))
# sock=socket.create_connection(("127.0.0.1", 10001))
text=str(input())
while text!='/e':
    sock.send(text.encode("utf8"))
    text = str(input())

sock.close()