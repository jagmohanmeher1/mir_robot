#!/usr/bin/env python3
"""
Mock rosbridge server for testing mir_driver without a real MiR robot.
This simulates the rosbridge WebSocket interface that a real MiR robot provides.
"""
import asyncio
import json
import time
import websockets
from datetime import datetime


class MockMiRRosbridgeServer:
    """Mock rosbridge server that simulates a MiR robot."""
    
    def __init__(self):
        self.clients = set()
        self.subscriptions = {}  # topic -> set of clients
        self.publishers = {}  # topic -> set of clients
        self.topic_types = {
            '/odom': 'nav_msgs/Odometry',
            '/scan': 'sensor_msgs/LaserScan',
            '/robot_state': 'mir_msgs/RobotState',
            '/robot_mode': 'mir_msgs/RobotMode',
            '/robot_pose': 'geometry_msgs/Pose',
            '/tf': 'tf2_msgs/TFMessage',
            '/tf_static': 'tf2_msgs/TFMessage',
            '/map': 'nav_msgs/OccupancyGrid',
            '/map_metadata': 'nav_msgs/MapMetaData',
            '/b_scan': 'sensor_msgs/LaserScan',
            '/f_scan': 'sensor_msgs/LaserScan',
            '/imu_data': 'sensor_msgs/Imu',
            '/diagnostics': 'diagnostic_msgs/DiagnosticArray',
            '/diagnostics_agg': 'diagnostic_msgs/DiagnosticArray',
            '/rosout': 'rosgraph_msgs/Log',
            '/rosout_agg': 'rosgraph_msgs/Log',
        }
        self.publishing_tasks = []
        
    async def handle_client(self, websocket, path):
        """Handle a new WebSocket client connection."""
        self.clients.add(websocket)
        print(f"[Mock Server] Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    print(f"[Mock Server] Invalid JSON: {message}")
                except Exception as e:
                    print(f"[Mock Server] Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            # Clean up subscriptions
            for topic, clients in list(self.subscriptions.items()):
                clients.discard(websocket)
            print(f"[Mock Server] Client disconnected: {websocket.remote_address}")
    
    async def handle_message(self, websocket, data):
        """Handle a message from a client."""
        op = data.get('op')
        
        if op == 'subscribe':
            topic = data.get('topic')
            if topic:
                if topic not in self.subscriptions:
                    self.subscriptions[topic] = set()
                self.subscriptions[topic].add(websocket)
                print(f"[Mock Server] Client subscribed to: {topic}")
                
        elif op == 'unsubscribe':
            topic = data.get('topic')
            if topic and topic in self.subscriptions:
                self.subscriptions[topic].discard(websocket)
                print(f"[Mock Server] Client unsubscribed from: {topic}")
                
        elif op == 'publish':
            topic = data.get('topic')
            msg = data.get('msg', {})
            if topic:
                if topic not in self.publishers:
                    self.publishers[topic] = set()
                self.publishers[topic].add(websocket)
                print(f"[Mock Server] Client publishing to: {topic}")
                
        elif op == 'call_service':
            service = data.get('service')
            service_id = data.get('id')
            
            if service == '/rosapi/topics':
                response = {
                    'op': 'service_response',
                    'id': service_id,
                    'values': {
                        'topics': list(self.topic_types.keys())
                    }
                }
                await websocket.send(json.dumps(response))
                
            elif service == '/rosapi/topic_type':
                topic = data.get('args', {}).get('topic', '')
                topic_type = self.topic_types.get(topic, '')
                response = {
                    'op': 'service_response',
                    'id': service_id,
                    'values': {'type': topic_type}
                }
                await websocket.send(json.dumps(response))
                
            elif service == '/rosapi/publishers':
                topic = data.get('args', {}).get('topic', '')
                has_publishers = topic in self.publishers and len(self.publishers[topic]) > 0
                response = {
                    'op': 'service_response',
                    'id': service_id,
                    'values': {
                        'publishers': [f'/mock_server'] if has_publishers else []
                    }
                }
                await websocket.send(json.dumps(response))
                
            elif service == '/rosapi/subscribers':
                topic = data.get('args', {}).get('topic', '')
                has_subscribers = topic in self.subscriptions and len(self.subscriptions[topic]) > 0
                response = {
                    'op': 'service_response',
                    'id': service_id,
                    'values': {
                        'subscribers': [f'/mock_server'] if has_subscribers else []
                    }
                }
                await websocket.send(json.dumps(response))
    
    def create_fake_odom(self):
        """Create a fake odometry message."""
        now = time.time()
        return {
            'header': {
                'stamp': {'sec': int(now), 'nanosec': int((now % 1) * 1e9)},
                'frame_id': 'odom'
            },
            'child_frame_id': 'base_link',
            'pose': {
                'pose': {
                    'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                    'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
                },
                'covariance': [0.0] * 36
            },
            'twist': {
                'twist': {
                    'linear': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                    'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}
                },
                'covariance': [0.0] * 36
            }
        }
    
    def create_fake_scan(self):
        """Create a fake laser scan message."""
        now = time.time()
        return {
            'header': {
                'stamp': {'sec': int(now), 'nanosec': int((now % 1) * 1e9)},
                'frame_id': 'laser_link'
            },
            'angle_min': -3.14,
            'angle_max': 3.14,
            'angle_increment': 0.01,
            'time_increment': 0.0,
            'scan_time': 0.1,
            'range_min': 0.1,
            'range_max': 10.0,
            'ranges': [2.0] * 360,
            'intensities': [1.0] * 360
        }
    
    async def publish_fake_data(self):
        """Periodically publish fake data to subscribed clients."""
        while True:
            await asyncio.sleep(0.1)  # 10 Hz
            
            # Publish odom
            if '/odom' in self.subscriptions:
                msg = self.create_fake_odom()
                for client in self.subscriptions['/odom']:
                    try:
                        await client.send(json.dumps({
                            'op': 'publish',
                            'topic': '/odom',
                            'msg': msg
                        }))
                    except:
                        pass
            
            # Publish scan
            if '/scan' in self.subscriptions:
                msg = self.create_fake_scan()
                for client in self.subscriptions['/scan']:
                    try:
                        await client.send(json.dumps({
                            'op': 'publish',
                            'topic': '/scan',
                            'msg': msg
                        }))
                    except:
                        pass
            
            # Publish b_scan and f_scan
            for topic in ['/b_scan', '/f_scan']:
                if topic in self.subscriptions:
                    msg = self.create_fake_scan()
                    msg['header']['frame_id'] = 'back_laser_link' if 'b_' in topic else 'front_laser_link'
                    for client in self.subscriptions[topic]:
                        try:
                            await client.send(json.dumps({
                                'op': 'publish',
                                'topic': topic,
                                'msg': msg
                            }))
                        except:
                            pass


async def main():
    """Start the mock rosbridge server."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--port',
        type=int,
        default=9091,
        help='WebSocket port (default 9091 avoids clash with other rosbridge on 9090)',
    )
    args, _unknown = parser.parse_known_args()

    server = MockMiRRosbridgeServer()

    # Start publishing task
    asyncio.create_task(server.publish_fake_data())

    # Start WebSocket server
    print(f'[Mock Server] Starting mock MiR rosbridge server on ws://localhost:{args.port}')
    print('[Mock Server] Connect mir_bridge_ros2.py with matching port, e.g. port:=9091')

    async with websockets.serve(server.handle_client, 'localhost', args.port):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Mock Server] Shutting down...")
