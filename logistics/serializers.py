from rest_framework import serializers

from .models import ContainerShipment, ContainerItem, StatusHistory


class ContainerItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerItem
        fields = "__all__"


class ContainerShipmentSerializer(serializers.ModelSerializer):
    items = ContainerItemSerializer(many=True, read_only=True)

    class Meta:
        model = ContainerShipment
        fields = "__all__"


class StatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusHistory
        fields = "__all__"
        read_only_fields = ["from_status"]

    def create(self, validated_data):
        shipment = validated_data["shipment"]
        from_status = shipment.status
        to_status = validated_data["to_status"]
        validated_data["from_status"] = from_status
        status_history = StatusHistory.objects.create(**validated_data)
        shipment.status = to_status
        shipment.save(update_fields=["status"])
        return status_history
