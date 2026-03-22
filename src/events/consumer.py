"""Kafka 消费者"""
import json
import logging
import asyncio
from typing import Any
from confluent_kafka import Consumer, KafkaError, Message, TopicPartition

from src.events.handlers.handler_registry import registry
from src.events.decoder import EventDecoder


logger = logging.getLogger(__name__)


class KafkaConsumer:
    """Kafka 消费者封装类 - 支持批量手动提交偏移量"""

    def __init__(self, configs: dict[str, Any]):
        self.topics = configs.get('topics', [])
        self.group_id = configs.get('group_id')
        self.running = False

        # 批量提交配置
        self.batch_size = configs.get('batch_size', 1)  # 每批消息数量
        self.batch_timeout_ms = configs.get('batch_timeout_ms', 5000)  # 批量超时时间
        self.max_retries = configs.get('max_retries', 3)  # 处理失败重试次数

        # 关闭自动提交，改为手动批量提交
        config = {
            'bootstrap.servers': configs.get("hosts"),
            'group.id': configs.get("group_id"),
            'auto.offset.reset': configs.get("auto_offset_reset", "latest"),
            'enable.auto.commit': False,  # 关闭自动提交
            'session.timeout.ms': configs.get("session_timeout_ms", 30000),
            'max.poll.interval.ms': configs.get("max_poll_interval_ms", 300000),
            'enable.partition.eof': False,
        }

        self.consumer = Consumer(config)

        # 批量处理状态
        self._message_buffer: list[Message] = []  # 消息缓冲区
        self._pending_offsets: dict[tuple[str, int], int] = {}  # 待提交的偏移量 { (topic, partition): offset }
        self._buffer_lock = asyncio.Lock()  # 缓冲区锁
        self._last_commit_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0

        logger.info(
            "Kafka 消费者已初始化: topics=%s, group_id=%s, batch_size=%d, "
            "batch_timeout_ms=%d",
            self.topics,
            self.group_id,
            self.batch_size,
            self.batch_timeout_ms
        )

    def subscribe(self) -> None:
        """订阅主题"""
        self.consumer.subscribe(self.topics)
        logger.info("已订阅主题: %s", self.topics)

    async def start(self) -> None:
        """启动消费者"""
        self.subscribe()
        self.running = True
        self._last_commit_time = asyncio.get_event_loop().time()
        logger.info("Kafka 消费者已启动，使用批量手动提交模式")

        try:
            while self.running:
                await self._poll_and_process_batch()
        except asyncio.CancelledError:
            logger.info("消费者任务被取消，正在优雅关闭...")
        except Exception as e:
            logger.error("消费者运行异常: %s", e, exc_info=True)
            raise
        finally:
            # 关闭前提交剩余偏移量
            await self._commit_pending_offsets(force=True)
            self.close()

    async def _poll_and_process_batch(self) -> None:
        """批量拉取并处理消息"""
        # 检查是否需要提交（超时或缓冲区已满）
        await self._check_and_commit()

        # 在线程池中执行阻塞的 poll 操作
        message = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.consumer.poll(timeout=1.0)
        )

        if message is None:
            return

        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                return
            else:
                logger.error("Kafka 错误: %s", message.error())
                return

        # 将消息加入缓冲区
        async with self._buffer_lock:
            self._message_buffer.append(message)

        # 如果缓冲区达到批次大小，立即处理
        if len(self._message_buffer) >= self.batch_size:
            await self._process_batch()

    async def _check_and_commit(self) -> None:
        """检查是否需要按超时提交偏移量"""
        now = asyncio.get_event_loop().time()
        elapsed_ms = (now - self._last_commit_time) * 1000
        if elapsed_ms >= self.batch_timeout_ms and self._pending_offsets:
            await self._commit_pending_offsets()

    async def _process_batch(self) -> None:
        """处理缓冲区中的批次消息"""
        async with self._buffer_lock:
            batch = self._message_buffer.copy()
            self._message_buffer.clear()

        if not batch:
            return

        logger.info("开始处理批次消息，消息数量: %d", len(batch))

        for message in batch:
            success = await self._process_message(message)
            if success:
                # 记录该分区处理成功的最大偏移量（+1 表示下次从下一条开始消费）
                key = (message.topic(), message.partition())
                self._pending_offsets[key] = max(
                    self._pending_offsets.get(key, -1),
                    message.offset() + 1
                )

        # 批次处理完成后提交偏移量
        await self._commit_pending_offsets()

    async def _commit_pending_offsets(self, force: bool = False) -> None:
        """提交待处理的偏移量"""
        if not self._pending_offsets:
            return

        offsets = [
            TopicPartition(topic, partition, offset)
            for (topic, partition), offset in self._pending_offsets.items()
        ]

        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.consumer.commit(offsets=offsets, asynchronous=True)
            )
            logger.info(
                "批量提交偏移量成功，涉及 %d 个分区",
                len(offsets)
            )
            self._pending_offsets.clear()
            self._last_commit_time = asyncio.get_event_loop().time()
        except Exception as e:
            logger.error("提交偏移量失败: %s", e, exc_info=True)

    async def _process_message(self, message: Message) -> bool:
        """
        处理单条消息
        
        支持的消息格式：
        - Header: 消息头，包含 Event-Id, Timestamp, Event-Type
        - Body: Base64 编码的 BaseEvent protobuf 消息
        - Payload: BaseEvent 中的 payload 字段包含具体事件内容
        
        编码格式：protobuf

        Args:
            message: Kafka 消息对象
        """
        topic = message.topic()
        partition = message.partition()
        offset = message.offset()
        key = message.key()
        value = message.value()

        raw_message: dict[str, Any] = {
            'topic': topic,
            'partition': partition,
            'offset': offset,
            'key': key.decode('utf-8') if key else None,
        }
        
        try:
            # 使用 EventDecoder 解码 protobuf 消息
            header, event = EventDecoder.decode_kafka_message(
                value,
                encoding="protobuf"
            )
            
            event_type = event.event_type
            
            logger.info(
                "接收到消息: topic=%s, partition=%d, offset=%d, "
                "event_type=%s, event_id=%s",
                topic,
                partition,
                offset,
                event_type,
                event.event_id
            )
            
            # 获取对应的处理器
            if not registry.has_handler(event_type):
                logger.warning(
                    "未找到事件类型 '%s' 的处理器，跳过处理",
                    event_type
                )
                return True  # 无处理器视为已消费，推进偏移量

            handler = registry.get_handler(event_type)

            # 执行处理器
            await handler.handle(event, raw_message)

            logger.debug(
                "事件处理完成: event_type=%s, event_id=%s",
                event_type,
                event.event_id
            )
            return True

        except json.JSONDecodeError as e:
            logger.error(
                "JSON 解析失败: %s, topic=%s, partition=%d, offset=%d",
                e,
                topic,
                partition,
                offset
            )
            return True  # 解析失败无法重试，跳过以推进偏移量
        except ValueError as e:
            logger.error(
                "消息格式错误: %s, topic=%s, partition=%d, offset=%d",
                e,
                topic,
                partition,
                offset
            )
            return True  # 格式错误无法重试，跳过以推进偏移量
        except Exception as e:
            logger.error(
                "事件处理异常: %s, topic=%s, partition=%d, offset=%d",
                e,
                topic,
                partition,
                offset,
                exc_info=True
            )
            return False  # 未知异常，不提交偏移量，等待重试

    def stop(self) -> None:
        """停止消费者"""
        logger.info("正在停止 Kafka 消费者...")
        self.running = False

    def close(self) -> None:
        """关闭消费者连接"""
        self.consumer.close()
        logger.info("Kafka 消费者已关闭")


def create_consumer_from_config(config: dict[str, Any]) -> KafkaConsumer:
    """
    从配置字典创建消费者实例
    
    Args:
        config: 配置字典，包含 kafka 配置信息
        
    Returns:
        KafkaConsumer 实例
    """
    return KafkaConsumer(configs=config)
