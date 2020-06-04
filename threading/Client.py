import socket
import threading
import os

# todo: принимать сообщения сервер
p_lock = threading.RLock()
server_adress = ("127.0.0.1", 10001)


def main():
    try:
        sock = socket.create_connection(server_adress)
        print('Your ip: {}'.format(sock.getsockname()))
    except socket.timeout or ConnectionRefusedError:
        exit('Server not found')
    except socket.error as ex:
        exit(f'Got unexpected error: {ex}')

    th_send_m = threading.Thread(target=send_msg, args=(sock,), name='TH_send_msg')
    th_recieve_m = threading.Thread(target=receive_msg, args=(sock,), name='TH_rec_msg')
    th_send_m.start()
    th_recieve_m.start()


def print_th(text):
    with p_lock:
        print(text)


def receive_msg(sock: socket.socket):
    while sock:
        try:
            data = sock.recv(1024)
        except ConnectionAbortedError:
            break
        except ConnectionResetError:
            print('Server disconnected')
            break
        except socket.error as ex:
            print("send data error:", ex)
            break
        if data:
            print(data.decode('utf8'))
    sock.close()
    exit()


def _process_request(conn, addr):
    with conn:
        while True:
            try:
                data = conn.recv(1024)
            except socket.timeout:
                print_th('close connection')
                break

            if not data or data.decode('utf8').strip() == '/e':
                print_th('{} go out'.format(addr))
                break
            print_th(data.decode('utf8'))
            # check_name(data.decode('utf8'), addr)


def send_msg(sock):
    text = str(input())
    while text != '/e':
        try:
            sock.send(text.encode("utf8"))
        except socket.timeout:
            print("send data timeout")
        except socket.error as ex:
            print("send data error:", ex)
            break
        text = str(input())
    try:
        sock.send(text.encode("utf8"))
    except ConnectionResetError:
        print('Server disconnected')
    except socket.error as ex:
        print("send data error:", ex)
    sock.close()
    exit()


if __name__ == '__main__':
    main()
