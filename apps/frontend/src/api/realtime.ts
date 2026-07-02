import { http } from "@/api/http";

export type WebSocketTicketResponse = {
  ticket: string;
  expiresAt: string;
};

export async function requestLayerWebSocketTicket(
  layerId: string,
): Promise<WebSocketTicketResponse> {
  const response = await http.post<WebSocketTicketResponse>(
    `/api/v1/ws/layers/${layerId}/ticket`,
  );
  return response.data;
}
