import threading
import socket
import ipaddress
import ssl


def port_scan(ip, port):
    """
    Функция, которая проверяет доступность порта и выводит на
    экран, в случае, если порт доступен

    Параметры
    ---------
    ip : IPv4Address
        ip-адресс сканируемой сети
    port : int
        Номер проверяемого порта

    Возвращает
    ----------
    None
    """
    host = (ip, port)
    # создаем сокет
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # устанавливаем время ожидания
    socket_.settimeout(0.5)

    if port == 443:
        try:
            # для 443 порта необходимо закрытое соединение (SSL)
            connection = socket.create_connection(host)
            print(ip, port, 'OPEN',  flush=True)
            message = b"HEAD / HTTP/1.1\r\nConnection: close\r\nHost: " + bytes(ip, 'utf-8') + b"\r\n\r\n"
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            socket_sock = context.wrap_socket(socket_, server_hostname=ip)
            socket_sock.connect(host)
            # отправка HEAD запроса
            socket_sock.send(message)
            # получение ответа
            info = str(socket_sock.recv(1024), 'utf-8')
            if info.find('Server') != -1:
                print(info[info.find('Server'):].split('\n')[0], flush=True)
            connection.close()
        except:
            pass
    else:
        try:
            connection = socket_.connect(host)
            print(ip, port, 'OPEN', flush=True)
            if port == 80:
                message = b"HEAD / HTTP/1.1\r\nHost: " + bytes(ip, 'utf-8') + b"\r\nAccept: text/html\r\n\r\n"
                # отправка HEAD запроса
                socket_.sendall(message)
                # получение ответа
                info = str(socket_.recv(1024), 'utf-8')
                if info.find('Server') != -1:
                    print(info[info.find('Server'):].split('\n')[0], flush=True)
            connection.close()
        except:
            pass


if __name__ == '__main__':
    ip_addresses = input('Enter the ip address range: \n(For example: 192.168.1.0/24)\n')
    # примеры адресов 195.154.180.82, 142.250.75.238
    ports = list(map(int, input('Enter the ports to check: \n(For example: 80, 443, 22, 21, 25)\n').split(', ')))
    for ip in ipaddress.IPv4Network(ip_addresses):
        for port in ports:
            # создание потоков
            thread = threading.Thread(target=port_scan, kwargs={'ip': str(ip), 'port': port})
            thread.start()
            thread.join()

