"""
Created on Tue Jul  7 11:20:01 2020

@author: Thien, Tien, Toan
"""

import socket
import signal # su dung Ctrl + C
import sys
import time
import threading

class WebServer(object):


    def __init__(self, port=80):    # nếu port 80 không dùng được thì thử port khác như 8080, 9123...
        self.flag=0
        self.host = "127.0.0.1" # gan ip host = local host
        self.port = port        # port = 8080
        self.content_dir = 'web_files' # nơi lưu trữ các tập tin web

    def start(self):
       
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #khoi tao socket nhan dia chi ipv4 va hoat dong tren giao thuc tcp
        
        try:
            print("Starting server on {host}:{port}".format(host=self.host, port=self.port))
            self.socket.bind((self.host, self.port))    # gan dia chi ip va port cho socket da khoi tao
            print("Server started on port {port}.".format(port=self.port))

        except Exception as e:
            print("Error: Could not bind to port {port}".format(port=self.port)) # tắt server nếu port không khả dụng
            self.shutdown()
            sys.exit(1)
    
        self._listen() # bat dau listening vao connection

    def shutdown(self):
       
        try:
            print("Shutting down server")
            self.socket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            pass 

    def _generate_headers(self, response_code):# khoi tao header
      
        header = ''
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'

        time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += 'Date: {now}\n'.format(now=time_now)
        header += 'Server: Simple-Python-Server\n'
        header += 'Connection: close\n\n'
        return header
    def _redirect(self, client, file_request):
        """ Ham thuc hien tao redirection header va gui lai cho client """
        
        header = 'HTTP/1.1 301 Moved Permanently\n'
        header += 'Location: /' + file_request + '\n\n'
        print("Response from server: Redirect to /", file_request, '\n')
        response = header.encode()
        client.send(response)
        client.close()
        return
    def _redirect2(self, client, file_request):
        response_header = self._generate_headers(404)
        response = response_header.encode() 
        try:
            f = open(self.content_dir + '/404.html', 'rb')
            response_data = f.read()
            response += response_data
            f.close()
        except Exception as e:
            pass
       
        client.send(response)
        client.close()    
    def _listen(self):
       
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept() # gán biến client = socket mo ra cho qua trinh trao doi du lieu
            client.settimeout(60)  # Thời gian mở tối đa của socket là 60s
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_client, args=(client, address)).start() # Tạo luồng mới để xử lý khi kết nối với một client mới

    def _handle_client(self, client, address):
   
        
        PACKET_SIZE = 1024
        while True:

            data = client.recv(PACKET_SIZE).decode() # nhan data packet và decode
            if not data: break

            request_method = data.split(' ')[0]  #lấy phương thức của gói tin request
            print("Request from client: {b}".format(b=data.split('\n')[0]))
            if self.flag == 2: 
            	self.flag=0
            	self._redirect2(client, '404.html')
            	break
            if request_method == "POST" :  #nếu phương thức = post, tiến hành kiểm tra username và password
                index1 = data.find('username',0,len(data))
                index1 = index1+9
                index2 = data.find('&',index1)
                s1 = data[index1:index2]
                s2 = data[index2+10:]
                if s1 == "admin" and s2 == "admin":
                    self.flag=1
                    self._redirect(client, 'infor.html')  #nếu nhập đúng -> chuyển hướng đến trang infor.html
                    break
                else:
                    self._redirect(client, '404.html')   #nếu nhập sai -> chuyển hướng đến trang 404.html
                    self.flag =2
                    break
            if request_method == "GET" or request_method == "HEAD":
                # Ex) "GET /index.html" split on space
                file_requested = data.split(' ')[1]  #lấy tên file mà client yêu cầu get

                # If get has parameters ('?'), ignore them
                file_requested =  file_requested.split('?')[0]
                if file_requested == "/":
                    self._redirect(client, 'index.html')    #nếu tên file là '/' -> chuyển hướng đến trang index
                    break
                if file_requested == "/infor.html" and self.flag == 0:   #Kiem tra login hay chưa, nếu chưa (flag=0) trả về web login ( index.html)
                    self._redirect(client, 'index.html')
                    break                
                if file_requested == "/index.html":     #set flag=0 khi quay lại trang login
                    self.flag=0
                if file_requested == "/infor.html":     #set flag=0 khi đã hiện lên trang infor.html ,
                	self.flag=0                         #tránh tình trạng login vào trình duyệt này nhưng truy cập trực tiếp info.html trên trình duyệt khác được
                filepath_to_serve = self.content_dir + file_requested

                # Load and Serve files content
                try:   # thực hiện đọc dữ liệu từ file nếu file tồn tại
                    f = open(filepath_to_serve, 'rb')
                    if request_method == "GET": # Read only for GET
                        response_data = f.read()
                    f.close()
                    response_header = self._generate_headers(200)   #tạo header 200: mã thành công
                    print("Response from server: Serving file [{fp}]".format(fp=filepath_to_serve))

                except Exception as e:   #file không tồn tại thì trả về lỗi 404
                    print("Response from server: File not found")
                    
                    response_header = self._generate_headers(404)   #tạo header 400: mã lỗi
                    f = open(self.content_dir + '/404.html', 'rb')
                    if request_method == "GET": 
                        response_data = f.read()
                    f.close()
                        
                response = response_header.encode()
                if request_method == "GET":
                    response += response_data
            

                client.send(response)   #gửi lại dữ liệu gồm header và data cho client
                client.close()          #đóng kết nối khi hoàn thành thao tác
                break
            else:
                print("Unknown HTTP request method: {method}".format(method=request_method))

def shutdownServer(sig, frame):
   
    print("beeep")
    server.shutdown()
    sys.exit(0)

server = WebServer(80)  # có thể nhập các port khác nếu không dùng được port 80
signal.signal(signal.SIGINT, shutdownServer)
print("Press Ctrl+C to shut down server.")
server.start()
