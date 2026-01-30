from django.contrib import admin

from .models import ChatMessage, ClientChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("shipment", "author", "site", "created_at")


@admin.register(ClientChatMessage)
class ClientChatMessageAdmin(admin.ModelAdmin):
    list_display = ("shipment", "author", "sender_type", "created_at")
