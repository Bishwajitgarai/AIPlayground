from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from app.services.redis_client import redis_client
from app.services.gemini_client import google_client
import asyncio,json,base64
from app.core.config import settings

ws_router = APIRouter(tags=["Live list"], prefix="/ws")

@ws_router.websocket("/stream/chat/{meeting_id}/")
async def receive_updates(websocket: WebSocket, meeting_id: str):
    print(f"📡 WebSocket connection recived for meeting: {meeting_id}")

    await websocket.accept()
    print(f"📡 WebSocket connected for meeting: {meeting_id}")
    channel_id=f"channel:meeting:{meeting_id}"

    # Subscribe to Redis channel (for sync Redis client)
    pubsub = redis_client.pubsub()
    await asyncio.to_thread(pubsub.subscribe, channel_id)
    print(f"✅ Subscribed to Redis channel: {channel_id}")

    connected = True

    async def listen_to_redis():
        """Listen for messages from Redis and send to WebSocket"""
        try:
            while connected:
                # Get message from Redis (sync call in thread)
                message = await asyncio.to_thread(
                    pubsub.get_message,
                    timeout=1.0
                )
                if message and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                        # print(f"📤 Sent Redis message to WebSocket: {data}")
                    except Exception as e:
                        print(f"⚠ Failed to send Redis message to WebSocket: {e}")
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error in Redis listener: {e}")

    async def listen_to_websocket():
        """Listen for messages from WebSocket and publish to Redis"""
        nonlocal connected
        try:
            while connected:
                # Receive message from WebSocket
                message = await websocket.receive_json()
                print(f"📥 Received message from WebSocket: {message}")
                
                # Publish to Redis (sync call in thread)
                if message:
                    await asyncio.to_thread(
                        redis_client.publish,
                        channel_id,
                        json.dumps(message)
                    )
                    # print(f"✅ Published WebSocket message to Redis: {message}")
        except WebSocketDisconnect:
            connected = False
            print(f"❌ WebSocket disconnected: {meeting_id}")
        except Exception as e:
            connected = False
            print(f"Error in WebSocket listener: {e}")

    try:
        # Run both listeners concurrently
        await asyncio.gather(
            listen_to_redis(),
            listen_to_websocket(),
            return_exceptions=True
        )
    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
    finally:
        connected = False
        # Clean up Redis connection (sync calls in thread)
        await asyncio.to_thread(pubsub.unsubscribe, f"channel:meeting:{meeting_id}")
        await asyncio.to_thread(pubsub.close)
        print(f"✅ Cleaned up Redis connection for meeting: {meeting_id}")    


@ws_router.websocket("/stream/{meeting_id}/")
async def stream_audio(websocket: WebSocket, meeting_id: str):
    # Extract system_instruction from query param if available
    print(f"🔌 WebSocket connection comes for meeting: {meeting_id}")

    query_params = websocket.query_params
    custom_instruction = query_params.get("system_instruction")
    default_system_instruction = """
        You are a meeting assistant listening to the real-time audio of a meeting.
        Your role is to silently observe and process the conversation as it happens. Do not respond unless:
        - Someone asks a clear and direct question.
        - You're prompted to assist or clarify something based on the meeting's context.
        Stay passive and non-intrusive. Only engage when your input is explicitly needed.
        Keep your responses concise, professional, and relevant to the conversation.
        """

    system_instruction = custom_instruction if custom_instruction else default_system_instruction
    system_instruction = system_instruction + "\n    When you reply, always end your response with the token |end| so the system knows your reply is complete. Do not include |end| in any other context."

    config = {
        "response_modalities": ["Text"],
        "input_audio_transcription": {},
        "system_instruction": system_instruction,
    }

    await websocket.accept()
    print(f"🔌 WebSocket connected for meeting: {meeting_id}")
    channel_id=f"channel:meeting:{meeting_id}"
    
    # Create Redis pubsub object
    pubsub = redis_client.pubsub()
    pubsub.subscribe(channel_id)

    try:
        pcm_queue = asyncio.Queue()
        session_active = True

        async def receive_redis_messages(session):
            """Receive messages from Redis and forward to Gemini session"""
            while session_active:
                try:
                    # Use non-blocking message check with async sleep
                    message = pubsub.get_message()
                    if message and message['type'] == 'message':
                        data = json.loads(message['data'])
                        print(f"📥 Received message from Redis: {data}")
                        
                        msg_type = data.get("type", "")
                        
                        if msg_type == "query":
                            prompt = data.get("text", "")
                            if prompt:
                                await session.send(input=prompt, end_of_turn=True)
                                # print(f"📤 Sent query to Gemini: {prompt[:50]}...")
                                
                        elif msg_type == "close":
                            print(f"🔌 Closing WebSocket connection for meeting: {meeting_id}")
                            break
                            
                    # Small sleep to prevent busy waiting
                    await asyncio.sleep(0.1)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"⚠ Redis message error: {e}")
                    await asyncio.sleep(0.1)

        async def receive_messages():
            """Receives JSON and puts audio chunks into PCM queue."""
            while True:
                try:
                    data = await websocket.receive_json()
                    msg_type = data.get("type")

                    if msg_type == "audio":
                        b64data = data.get("data")
                        if b64data:
                            pcm_data = base64.b64decode(b64data)
                            await pcm_queue.put(pcm_data)
                    elif msg_type == "text":
                        text = data.get("text", "")
                        if not text:
                            print("⚠ No text provided in message")
                            continue
                        else:
                            prompt = (
                                f"The question is: {text.strip()} \n Provide a concise answer based on the audio content heard so far."
                            )
                        end_of_turn = data.get("end_of_turn", False)
                        await session.send(input=prompt, end_of_turn=end_of_turn)
                        
                    elif msg_type == "pause":
                        print("⏸ Received pause message")
                        # Synchronous Redis publish
                        try:
                            redis_client.publish(
                                channel_id,
                                json.dumps({
                                    "type": "pause",
                                    "text": "Transcription paused."
                                })
                            )
                        except Exception as e:
                            print(f"⚠ Failed to publish pause message: {e}")

                    elif msg_type == "resume":
                        print("▶ Received resume message")
                        try:
                            redis_client.publish(
                                channel_id,
                                json.dumps({
                                    "type": "resume",
                                    "text": "Transcription resumed."
                                })
                            )
                        except Exception as e:
                            print(f"⚠ Failed to publish resume message: {e}")
                    
                    else:
                        print("⚠ Unknown message type:", msg_type)

                except WebSocketDisconnect:
                    print(f"❌ WebSocket disconnected: {meeting_id}")
                    # Synchronous Redis publish
                    redis_client.publish(
                        channel_id,
                        json.dumps({
                            "type": "close",
                            "message": "Manager has closed the connection."
                        })
                    )
                    break
                except Exception as e:
                    print(f"⚠ Error receiving message: {e}")
                    break

        async def audio_stream():
            """Yields PCM data chunks for Gemini start_stream()."""
            while True:
                chunk = await pcm_queue.get()
                yield chunk
                pcm_queue.task_done()

        async with google_client.aio.live.connect(model=settings.GEMINI_LIVE_MODEL, config=config) as session:
            print(f"🎤 Gemini session started for meeting: {meeting_id}")
            
            # Send initial system instruction
            # await session.send(input=system_instruction)

            # Start tasks
            stream_task = asyncio.create_task(receive_messages())
            redis_task = asyncio.create_task(receive_redis_messages(session=session))
            buffer = ""

            # Start Gemini stream
            async for response in session.start_stream(
                stream=audio_stream(),
                mime_type="audio/pcm"
            ):
                if response.text:
                    buffer += response.text

                    if "|end|" in buffer:
                        # Extract complete response and strip the marker
                        final_text = buffer.replace("|end|", "").strip()

                        # Synchronous Redis publish
                        redis_client.publish(
                            channel_id,
                            json.dumps({
                                "type": "answer",
                                "text": final_text
                            })
                        )
                        print(f"📤 Published answer to Redis: {final_text[:50]}...")
                        buffer = ""  # Reset for the next message
            
            # Wait for tasks to complete
            session_active = False
            await stream_task
            await redis_task
            
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected in Live: {meeting_id}")
        # Synchronous Redis publish
        redis_client.publish(
            channel_id,
            json.dumps({
                "type": "close",
                "message": "Manager has closed the connection."
            })
        )
    except Exception as e:
        print(f"⚠ Gemini session error for meeting {meeting_id}: {e}")
    finally:
        # Cleanup Redis subscription
        pubsub.unsubscribe(f"channel:meeting:{meeting_id}")
        pubsub.close()