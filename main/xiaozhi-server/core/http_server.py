import asyncio
from aiohttp import web
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler

TAG = __name__


class SimpleHttpServer:
    def __init__(self, config: dict, ws_server=None):
        self.config = config
        self.ws_server = ws_server
        self.logger = setup_logging()
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config)

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        """获取websocket地址

        Args:
            local_ip: 本地IP地址
            port: 端口号

        Returns:
            str: websocket地址
        """
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket")

        if websocket_config and "你" not in websocket_config:
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    async def handle_broadcast_message(self, request):
        """处理广播消息请求"""
        try:
            # 检查WebSocket服务器是否可用
            if not self.ws_server:
                return web.json_response(
                    {"status": "error", "message": "WebSocket服务器不可用"}, 
                    status=500
                )

            # 解析请求数据
            if request.content_type == 'application/json':
                data = await request.json()
            else:
                # 支持表单数据
                data = await request.post()
                data = dict(data)

            # 获取消息内容
            text = data.get('text', '') or data.get('message', '')
            device_id = data.get('device_id', None)
            
            if not text:
                return web.json_response(
                    {"status": "error", "message": "消息内容不能为空"}, 
                    status=400
                )

            # 记录接收到的请求
            client_ip = request.remote
            self.logger.bind(tag=TAG).info(f"收到来自 {client_ip} 的广播请求: {text}")

            # 执行广播
            if device_id:
                # 发送到指定设备
                success = await self.ws_server.send_message_to_device(device_id, text)
                if success:
                    return web.json_response({
                        "status": "success", 
                        "message": f"消息已发送到设备 {device_id}",
                        "data": {
                            "text": text,
                            "device_id": device_id,
                            "sent_count": 1
                        }
                    })
                else:
                    return web.json_response(
                        {"status": "error", "message": f"设备 {device_id} 未找到或未连接"}, 
                        status=404
                    )
            else:
                # 广播到所有设备
                success_count = await self.ws_server.broadcast_message_to_all(text)
                return web.json_response({
                    "status": "success", 
                    "message": f"消息已广播到 {success_count} 个设备",
                    "data": {
                        "text": text,
                        "sent_count": success_count,
                        "total_connections": len(self.ws_server.active_connections)
                    }
                })
                
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"处理广播消息请求失败: {e}")
            return web.json_response(
                {"status": "error", "message": f"服务器内部错误: {str(e)}"}, 
                status=500
            )

    async def handle_get_status(self, request):
        """获取服务器状态"""
        try:
            if not self.ws_server:
                return web.json_response(
                    {"status": "error", "message": "WebSocket服务器不可用"}, 
                    status=500
                )

            active_connections = len(self.ws_server.active_connections)
            device_list = []
            
            for handler in self.ws_server.active_connections:
                try:
                    device_info = {
                        "device_id": getattr(handler, 'device_id', 'unknown'),
                        "client_ip": getattr(handler, 'client_ip', 'unknown'),
                        "session_id": getattr(handler, 'session_id', 'unknown')
                    }
                    device_list.append(device_info)
                except Exception:
                    continue

            return web.json_response({
                "status": "success",
                "data": {
                    "active_connections": active_connections,
                    "devices": device_list,
                    "server_time": asyncio.get_event_loop().time()
                }
            })
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"获取服务器状态失败: {e}")
            return web.json_response(
                {"status": "error", "message": f"获取状态失败: {str(e)}"}, 
                status=500
            )

    async def _handle_cors(self, request):
        """处理CORS预检请求"""
        return web.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )

    async def start(self):
        server_config = self.config["server"]
        read_config_from_api = self.config.get("read_config_from_api", False)
        host = server_config.get("ip", "0.0.0.0")
        port = int(server_config.get("http_port", 8003))

        if port:
            app = web.Application()

            if not read_config_from_api:
                # 如果没有开启智控台，只是单模块运行，就需要再添加简单OTA接口，用于下发websocket接口
                app.add_routes(
                    [
                        web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                        web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                        web.options("/xiaozhi/ota/", self.ota_handler.handle_post),
                    ]
                )
            # 添加路由
            app.add_routes(
                [
                    web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                    web.post("/mcp/vision/explain", self.vision_handler.handle_post),
                    web.options("/mcp/vision/explain", self.vision_handler.handle_post),
                    # 添加广播消息接口
                    web.post("/api/broadcast", self.handle_broadcast_message),
                    web.get("/api/status", self.handle_get_status),
                    web.options("/api/broadcast", self._handle_cors),
                    web.options("/api/status", self._handle_cors),
                ]
            )

            # 运行服务
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()

            # 保持服务运行
            while True:
                await asyncio.sleep(3600)  # 每隔 1 小时检查一次
