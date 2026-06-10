from ...models.message import Message


class MemoryWriter:

    def store_message(self, conversation, role, content):
        Message.objects.create(
            conversation=conversation, role=role, content={"text": content}
        )
