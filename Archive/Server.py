import socket
import threading
import os
import multiprocessing
# todo: asyncio
# todo: connection with client
# todo: create users database
# todo: message types
# todo: commands
# todo: raspberry?)

# conn.settimeout(1)#timeout for connection
memory = dict()
m_lock = threading.RLock()
p_lock = threading.RLock()


def process_request(conn, addr):
    print('Connected client: {} to {} pid'.format(addr, os.getpid()))

    with conn:
        conn.sendto("Добро пожаловать на супер чат! введите имя через 'name:'\n".encode('utf8'), addr)
        info='Ваш id: {}'.format(addr)
        conn.sendto(info.encode('utf8'), addr)
        while True:
            try:
                data = conn.recv(1024)
            except socket.timeout:
                print_th('close connection')
                break

            if not data or data.decode('utf8').strip() == '/e':

                print_th('{} go out'.format(addr))
                break
            print_th(check_name(data.decode('utf8'), addr))
            conn.sendto(data, ('0.0.0.0', 0))
            # check_name(data.decode('utf8'), addr)


def check_name(text, addr):
    if text[:5] == 'name:':
        database('add', addr, text[5:].strip())
        return f'Your name: {text[5:].strip()}'
    else:
        if database('check', addr):
            return ('{id} > {mes}'.format(mes=text, id=memory[addr]))
        else:
            return ('{id} > {mes}'.format(mes=text, id=addr))


def database(op, addr, name=None):
    with m_lock:
        if op == 'check':
            return addr in memory
        elif op == 'add':
            memory[addr] = name
            return None


def print_th(text):

    with p_lock:
        print(text)

def worker(sock):
    while True:
        conn, addr = sock.accept()
        # print("pid", os.getpid())
        th = threading.Thread(target=process_request, args=(conn, addr))
        th.start()

def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 10001))
        sock.listen(socket.SOMAXCONN)
        print_th('Main pid: {}'.format(os.getpid()))

        workers_count = 3
        workers_list = [multiprocessing.Process(target=worker, args=(sock,))
                        for _ in range(workers_count)]

        for w in workers_list:
            w.start()

        for w in workers_list:
            w.join()



if __name__ == '__main__':
    main()
