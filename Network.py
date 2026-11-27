import json
import queue
import socket
import threading
from websockets.sync.server import serve
from websockets.sync.client import connect

DefaultPort = 8765

# Tamano maximo del buffer antes de obligar a enviar (el "MSS" del algoritmo de Nagle)
MSS = 1024


def GetLocalIP():
    try:
        Sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        Sock.connect(("8.8.8.8", 80))
        IP = Sock.getsockname()[0]
        Sock.close()
        return IP
    except Exception:
        return "127.0.0.1"


# Principio del algoritmo de Nagle (RFC 896) aplicado a los mensajes del juego:
# - Si no hay nada pendiente de confirmar (ACK), el mensaje se envia de inmediato.
# - Si ya hay un paquete en camino sin ACK, los mensajes chicos se acumulan en un buffer.
# - El buffer se envia junto en un solo paquete cuando llega el ACK
#   o cuando el buffer ya llena un segmento completo (MSS).
class NagleSender:
    def __init__(self, Socket):
        self.Socket = Socket
        self.Buffer = []
        self.BufferSize = 0
        self.WaitingAck = False
        self.Seq = 0
        self.BufferLock = threading.Lock()
        self.SendLock = threading.Lock()

    def SendRaw(self, Packet):
        with self.SendLock:
            self.Socket.send(json.dumps(Packet))

    def Send(self, Message):
        with self.BufferLock:
            self.Buffer.append(Message)
            self.BufferSize += len(json.dumps(Message))
            self.TryFlush()

    def OnAck(self):
        with self.BufferLock:
            self.WaitingAck = False
            self.TryFlush()

    def TryFlush(self):
        if len(self.Buffer) == 0:
            return
        if self.WaitingAck and self.BufferSize < MSS:
            return

        Packet = {"Type": "Batch", "Seq": self.Seq, "Messages": self.Buffer}
        try:
            self.SendRaw(Packet)
        except Exception:
            return

        self.Seq += 1
        self.Buffer = []
        self.BufferSize = 0
        self.WaitingAck = True


class Connection:
    def __init__(self):
        self.Inbox = queue.Queue()
        self.Sender = None
        self.Socket = None
        self.Server = None
        self.Role = None
        self.Connected = False

    def Host(self, Port = DefaultPort):
        self.Role = "host"
        Thread = threading.Thread(target = self.RunHost, args = (Port,), daemon = True)
        Thread.start()

    def Join(self, Address):
        self.Role = "client"
        if ":" not in Address:
            Address = Address + ":" + str(DefaultPort)
        Thread = threading.Thread(target = self.RunClient, args = (Address,), daemon = True)
        Thread.start()

    def RunHost(self, Port):
        def Handler(Socket):
            # Solo se acepta un rival
            if self.Connected:
                Socket.close()
                return
            self.Socket = Socket
            self.Sender = NagleSender(Socket)
            self.Connected = True
            self.Inbox.put({"Type": "Connected"})
            self.Listen(Socket)

        try:
            self.Server = serve(Handler, "0.0.0.0", Port)
            self.Server.serve_forever()
        except Exception as error:
            self.Inbox.put({"Type": "Error", "Text": str(error)})

    def RunClient(self, Address):
        try:
            Socket = connect("ws://" + Address)
        except Exception as error:
            self.Inbox.put({"Type": "Error", "Text": str(error)})
            return

        self.Socket = Socket
        self.Sender = NagleSender(Socket)
        self.Connected = True
        self.Inbox.put({"Type": "Connected"})
        self.Listen(Socket)

    # Hilo que recibe: confirma cada paquete con un ACK inmediato y reparte los mensajes
    def Listen(self, Socket):
        try:
            for Raw in Socket:
                Packet = json.loads(Raw)
                if Packet["Type"] == "Ack":
                    self.Sender.OnAck()
                elif Packet["Type"] == "Batch":
                    self.Sender.SendRaw({"Type": "Ack", "Seq": Packet["Seq"]})
                    for Message in Packet["Messages"]:
                        self.Inbox.put(Message)
        except Exception:
            pass
        finally:
            self.Connected = False
            self.Inbox.put({"Type": "Disconnected"})

    def Send(self, Message):
        if self.Sender is not None and self.Connected:
            self.Sender.Send(Message)

    def Close(self):
        self.Connected = False
        try:
            if self.Socket is not None:
                self.Socket.close()
        except Exception:
            pass
        try:
            if self.Server is not None:
                self.Server.shutdown()
        except Exception:
            pass