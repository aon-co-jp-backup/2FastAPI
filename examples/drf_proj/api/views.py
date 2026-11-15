from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

NOTES = {1: {"id": 1, "text": "first"}, 2: {"id": 2, "text": "second"}}


class NoteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=20)
    done = serializers.BooleanField(required=False, default=False)
    priority = serializers.IntegerField(required=False)
    ratio = serializers.FloatField(min_value=0, max_value=1, default=0.5)


@api_view(["GET"])
def ping(request):
    return Response({"ok": True})


@api_view(["GET", "POST"])
def echo(request):
    if request.method == "POST":
        name = request.data.get("name", "anon")
        return Response({"hello": name}, status=status.HTTP_201_CREATED)
    q = request.query_params.get("q", "none")
    return Response({"q": q})


@api_view(["GET"])
@permission_classes([AllowAny])
def thing(request, pk):
    if pk == 9:
        return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"pk": pk})


@api_view(["POST"])
def make(request):
    ser = NoteSerializer(data=request.data)
    if ser.is_valid():
        return Response(ser.validated_data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class Notes(APIView):
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        return Response(list(NOTES.values())[:limit])

    def post(self, request):
        text = request.data.get("text")
        if not text:
            return Response({"error": "text required"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"id": 3, "text": text}, status=status.HTTP_201_CREATED)


class NoteDetail(APIView):
    def get(self, request, pk):
        if pk not in NOTES:
            return Response({"error": "no such note"}, status=status.HTTP_404_NOT_FOUND)
        return Response(NOTES[pk])

    def delete(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)
